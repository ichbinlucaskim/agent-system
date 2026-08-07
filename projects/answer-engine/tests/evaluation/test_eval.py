from answer_engine.evaluation.runner import load_cases, run_suite_offline


def test_offline_suite():
    report = run_suite_offline()
    assert report["total"] == len(load_cases())
    failed = [r for r in report["results"] if not r["passed"]]
    assert not failed, failed
