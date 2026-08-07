"""Routing and policy retrieval."""

from __future__ import annotations

from support_desk.tools_gate.retrieve import build_policy_store, search_policy
from support_desk.routing.route import route


def test_route_faq_vs_account():
    assert route("How many days do I have to return an item?") == "faq"
    assert route("Please refund order ORD-100") == "account"
    assert route("Cancel my order before it ships") == "account"


def test_policy_search_finds_thirty_day_window():
    store = build_policy_store()
    hits = search_policy(store, "refund window days after delivery", k=3)
    assert hits
    blob = " ".join(hit.text for hit in hits)
    assert "30" in blob
