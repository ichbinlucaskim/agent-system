"""Lab 03 - Routing (reference solution).

A router classifies each request with a small model call, then dispatches it
to a handler built for that kind of request. The label set is closed, the
fallback is explicit, and the misroute rate is measured against labelled
data rather than guessed.
"""

from __future__ import annotations

from typing import Any

from common.client import complete, text_of

# Route name to the specialized system prompt that handles it. The 'other'
# entry is not decoration: a classifier that must choose will always choose,
# so input that fits no route needs somewhere honest to land.
ROUTES: dict[str, str] = {
    "refund": (
        "You handle refund and return questions for an online store. Policy: "
        "returns are accepted within 30 days of delivery and refunds are "
        "issued within 5 business days of receipt. Answer warmly, state the "
        "relevant policy, and tell the customer the exact next step to take."
    ),
    "technical": (
        "You are a technical support engineer for consumer hardware. Ask for "
        "the model number if it is missing, then walk through the most likely "
        "fixes one at a time, starting with the least invasive. Be precise "
        "and never invent a procedure you are not sure of."
    ),
    "marketing": (
        "You write marketing copy on request. Match the tone the user asks "
        "for, keep the copy tight, and offer exactly one alternative "
        "headline alongside the main draft."
    ),
    "other": (
        "You are a general assistant for an online store. The request did "
        "not match a specialized queue. Answer briefly if you safely can, "
        "and otherwise ask one clarifying question to find out what the "
        "customer needs."
    ),
}


# Where two routes could both apply, someone has to decide which one wins. A
# classifier cannot resolve an overlap nobody has settled, so the decisions are
# written down here, fed to the classifier, and encoded in LABELLED_SET below.
# Most misroutes are fixed by changing a rule here, not by changing the model.
ROUTE_BOUNDARIES: tuple[str, ...] = (
    "A request to get money back is 'refund', even when a fault caused it.",
    "A request to diagnose or fix a device is 'technical', even when the "
    "device is under warranty.",
    "A request to write or reword text for an audience is 'marketing', even "
    "when the subject is a policy or a support page.",
    "A problem with the website or with checkout is 'other'. The technical "
    "queue covers physical hardware only.",
    "An order that is missing, late, or untracked is 'other' until the "
    "customer asks for money back.",
)


def classify(question: str) -> str:
    """Return exactly one route name from ROUTES, falling back to 'other'."""
    labels = ", ".join(sorted(ROUTES))
    rules = "\n".join(f"- {rule}" for rule in ROUTE_BOUNDARIES)
    # The classifier's output space is tiny, so it stays cheap: low effort,
    # a short prompt, and a one-word answer.
    system = (
        "You are a request router. Read the user's message and respond with "
        f"exactly one label from this list and nothing else: {labels}. "
        "Use 'other' when no label clearly fits.\n\n"
        f"Rules for a request that could fit two labels:\n{rules}"
    )
    response = complete([{"role": "user", "content": question}], system=system)
    label = text_of(response).strip().lower()
    # The label is model output and therefore untrusted. Anything outside
    # the closed set falls back to 'other' instead of reaching dispatch.
    return label if label in ROUTES else "other"


def handle(route: str, question: str) -> str:
    """Answer the question using the system prompt for the given route."""
    # An unknown route lands on the fallback prompt rather than raising:
    # by the time we are here, failing loudly only punishes the customer.
    system = ROUTES.get(route, ROUTES["other"])
    response = complete([{"role": "user", "content": question}], system=system)
    return text_of(response)


def route_and_answer(question: str) -> dict[str, Any]:
    """Classify, dispatch, and report both the answer and the route taken."""
    route = classify(question)
    # The route rides along with the answer so callers and logs can see the
    # decision. Silent routing is how misroutes go unnoticed for months.
    return {"route": route, "answer": handle(route, question)}


def misroute_rate(labelled: list[tuple[str, str]]) -> float:
    """Fraction of labelled questions the classifier sends to the wrong route."""
    if not labelled:
        return 0.0
    wrong = sum(
        1 for question, expected in labelled if classify(question) != expected
    )
    return wrong / len(labelled)


# Labelled (question, expected_route) pairs covering every route. Run
# misroute_rate(LABELLED_SET) and record the number here after any change to
# ROUTES, ROUTE_BOUNDARIES, or the classifier prompt; that number is the
# baseline the change is judged against.
#
# Measured baseline: 0.00 over these 21 questions on the default model. Two of
# the boundary cases only land correctly because ROUTE_BOUNDARIES states the
# decision. With those rules removed the same classifier sends the broken
# refund button to 'technical' and the missing order to 'refund', which is a
# rate of about 0.10. The rules earned that, not the model.
LABELLED_SET: list[tuple[str, str]] = [
    ("I want my money back for the blender I bought last week.", "refund"),
    ("The package arrived damaged, can I send it back?", "refund"),
    ("How long do refunds take once you receive the return?", "refund"),
    ("Can I still return headphones I opened 10 days ago?", "refund"),
    ("My router keeps dropping the wifi connection every hour.", "technical"),
    ("The screen shows a blinking red light and will not boot.", "technical"),
    ("How do I reset the device to factory settings?", "technical"),
    ("Firmware update fails at 60 percent every time.", "technical"),
    ("Write a catchy tagline for our new espresso machine.", "marketing"),
    ("Draft a product description for a waterproof speaker.", "marketing"),
    ("We need a punchy subject line for the spring sale email.", "marketing"),
    ("What are your opening hours on public holidays?", "other"),
    ("Do you offer gift wrapping at checkout?", "other"),
    ("Tell me a fun fact about espresso.", "other"),
    # Boundary cases. Each one could read as two routes, and each label below
    # is a decision from ROUTE_BOUNDARIES rather than an obvious reading. These
    # are the rows that move the rate when a rule or a route prompt changes;
    # a set of only clear-cut questions scores well and detects nothing.
    ("My blender broke, I want my money back.", "refund"),
    ("My order is two weeks late, I want my money back.", "refund"),
    ("The speaker is still under warranty and will not charge.", "technical"),
    ("Write copy explaining our 30-day return policy.", "marketing"),
    ("I need a headline for our tech support page.", "marketing"),
    ("The refund button on your site does not work.", "other"),
    ("My order never arrived. What now?", "other"),
]


def main() -> int:
    """Route a few questions, then measure the misroute rate."""
    samples = [
        "My money back please, the toaster died after two days.",
        "The firmware update bricked my camera.",
        "Write me a slogan for a solar-powered lamp.",
    ]
    for question in samples:
        result = route_and_answer(question)
        print(f"user      {question}")
        print(f"route     {result['route']}")
        print(f"assistant {result['answer']}\n")

    rate = misroute_rate(LABELLED_SET)
    print(f"misroute rate over {len(LABELLED_SET)} labelled questions: {rate:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
