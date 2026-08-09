"""CLI: eval / smoke / audit-demo / chat.

Purpose
    모델 없이 eval·smoke·감사 스토리를 먼저 돌리고, 필요 시 chat으로 붙인다.

Why
    게이트가 모델 없이도 동작하는지 로컬에서 바로 확인하기 위함이다.

Trade-offs
    chat는 API 키가 필요하다. eval은 키가 없다.

Edges
    smoke는 PII 마스킹·한도 차단·금지 tool만 검사한다.
"""

from __future__ import annotations

import argparse
import json
import sys

from regulated_transfer.evaluation.runner import run_eval
from regulated_transfer.tools_gate import db
from regulated_transfer.tools_gate.pii import mask_account_id, mask_pii, mask_rrn
from regulated_transfer.tools_gate.policy_gate import audit_story_for_transfer, run_tool
from regulated_transfer.tools_gate.session import SessionContext
from regulated_transfer.tools_gate.tools import tool_schemas_for_session


def cmd_eval(_: argparse.Namespace) -> int:
    summary = run_eval()
    for r in summary["results"]:
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"[{mark}] {r['id']} {r['title']} → {r['outcome']} (기대: {r['expected']})")
    print(f"\n합계: {summary['passed']}/{summary['total']} 통과")
    return 0 if summary["failed"] == 0 else 1


def cmd_smoke(_: argparse.Namespace) -> int:
    """모델 없는 스모크 — 한도·PII·세션 tool 노출."""
    errors: list[str] = []

    raw_rrn = "900101-1234567"
    if mask_rrn(raw_rrn) == raw_rrn or "1234567" in mask_rrn(raw_rrn):
        errors.append("주민번호 마스킹 실패")
    acc = "110-123-456789"
    masked_acc = mask_account_id(acc)
    if acc in masked_acc or "456789" in masked_acc and "****" not in masked_acc:
        # 끝 4자리만 허용
        if not masked_acc.endswith("6789"):
            errors.append("계좌 마스킹 실패")

    conn = db.connect()
    ctx = SessionContext(customer_id="C-100", verified=True, connection=conn)
    blocked = run_tool(
        "transfer",
        {
            "from_account": "110-123-456789",
            "to_account": "110-987-654321",
            "amount_krw": 2_000_000,
        },
        ctx,
        approver=lambda _p: True,
    )
    if blocked["executed"]:
        errors.append("한도 초과 이체가 실행되면 안 됨")

    forbidden = run_tool(
        "wipe_customer",
        {"customer_id": "C-100"},
        ctx,
        approver=lambda _p: True,
    )
    if forbidden["executed"]:
        errors.append("금지 tool이 실행되면 안 됨")

    unverified_tools = {t["name"] for t in tool_schemas_for_session(False)}
    if "transfer" in unverified_tools or "lookup_balance" in unverified_tools:
        errors.append("미확인 세션에 이체/잔액 tool이 노출되면 안 됨")

    # 감사 payload에 계좌 원문이 없어야 함
    story = audit_story_for_transfer(ctx)
    if "110-123-456789" in story:
        errors.append("감사 스토리에 계좌 원문이 남음")
    if "900101-1234567" in mask_pii(story):
        errors.append("PII 원문이 스토리에 남음")

    if errors:
        print("SMOKE FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("SMOKE PASS")
    return 0


def cmd_audit_demo(_: argparse.Namespace) -> int:
    """한 건 이체의 감사 스토리를 출력한다."""
    conn = db.connect()
    ctx = SessionContext(customer_id="C-100", verified=True, connection=conn)
    record = run_tool(
        "transfer",
        {
            "from_account": "110-123-456789",
            "to_account": "110-987-654321",
            "amount_krw": 200_000,
        },
        ctx,
        approver=lambda prompt: (print(prompt), True)[1],
    )
    ctx.stop_reason = "completed" if record["executed"] else "blocked"
    print("=== 이체 실행 결과 ===")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    print("\n=== 감사 스토리 ===")
    print(audit_story_for_transfer(ctx))
    print(
        "\n참고: 이체는 confirm 등급이라 승인자가 decided_by=human_approver로 "
        "남고, 금액·잔액·1회/1일 한도는 tool 사전조건이 검사한다. "
        "로그의 계좌는 마스킹된다."
    )
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    from regulated_transfer.agent.loop import run_agent

    conn = db.connect()
    ctx = SessionContext(
        customer_id=args.customer_id,
        verified=not args.unverified,
        connection=conn,
    )

    def approver(prompt: str) -> bool:
        print(prompt)
        ans = input("승인합니까? [y/N] ").strip().lower()
        return ans in {"y", "yes", "예"}

    result = run_agent(args.message, ctx, approver=approver)
    print(result["final_text"])
    print(f"\nstop_reason={result['stop_reason']} steps={result['steps']}")
    print("\n--- 감사 스토리 ---")
    print(audit_story_for_transfer(ctx))
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="규제이체 데스크 — 이체 에이전트 학습용 연습")
    sub = parser.add_subparsers(dest="command", required=True)

    p_eval = sub.add_parser("eval", help="오프라인 action eval (거절·이관=성공)")
    p_eval.set_defaults(func=cmd_eval)

    p_smoke = sub.add_parser("smoke", help="모델 없는 스모크")
    p_smoke.set_defaults(func=cmd_smoke)

    p_audit = sub.add_parser("audit-demo", help="이체 1건 감사 스토리 출력")
    p_audit.set_defaults(func=cmd_audit_demo)

    p_chat = sub.add_parser("chat", help="모델 연동 대화 (API 키 필요)")
    p_chat.add_argument("message", help="고객 메시지")
    p_chat.add_argument("--customer-id", default="C-100")
    p_chat.add_argument("--unverified", action="store_true", help="본인확인 안 된 세션")
    p_chat.set_defaults(func=cmd_chat)

    args = parser.parse_args(argv)
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
