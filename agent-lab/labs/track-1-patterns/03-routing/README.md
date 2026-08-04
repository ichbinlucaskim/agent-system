# Lab 03 - Routing

## Goal

After this lab you can classify an incoming request and dispatch it to one of several specialized prompts or models, provide a safe fallback route, and measure the misroute rate on a labelled set.

## Prerequisites

Labs 00 through 02. Concepts: classification prompts, and the idea that different request types deserve different handling.

## Estimated time

30 to 45 minutes

## Background

Routing splits an input stream by kind and sends each kind to a handler built for it. A refund question, a technical troubleshooting question, and a request to write marketing copy have almost nothing in common, and one prompt that tries to serve all three ends up serving none of them well.

The classifier is itself a model call, and it is usually a small one. It reads the request and returns a single label from a closed set. Because its output space is tiny, it can run at a lower effort setting, or on a cheaper model, than the handlers it feeds.

Routing also lets you match cost to difficulty. Simple, high-volume requests can go to a fast model, and only the hard route pays for the expensive one. That is often the largest single cost lever in a production system, and it requires no change to the handlers themselves.

Every router needs a fallback. A classifier that must choose will always choose, even for input that fits no route, so give it an explicit `other` label and decide what happens there: a general handler, a clarifying question, or a refusal. Silent misrouting is worse than an honest fallback.

A misroute rate is only meaningful against labelled data. Write down thirty or so requests with the route each one should take, run the classifier over them, and count disagreements. That number is your baseline. Without it, a change to the classification prompt is a guess, and you will not know whether you improved anything.

## Steps

1. Define `ROUTES`: a dict mapping each route name to the specialized system prompt that handles it, including an `other` fallback. Then define `ROUTE_BOUNDARIES`: the rule that decides each case where two routes could both apply. A classifier cannot resolve an overlap nobody has settled.
2. Implement `classify`: one model call that returns exactly one route name. Give it the closed label list and the boundary rules. Validate the returned label against `ROUTES` and fall back to `other` when it does not match.
3. Implement `handle`: dispatch to the system prompt for the chosen route and return the answer.
4. Implement `route_and_answer`: classify, dispatch, and return both the answer and the route taken, so the decision is visible to callers and to logs.
5. Implement `misroute_rate`: run `classify` over a labelled list of `(question, expected_route)` pairs and return the fraction that disagree.
6. Populate `LABELLED_SET` with at least a dozen examples covering every route including `other`, add the boundary cases your rules decide, and record your baseline misroute rate in a comment. A set of only clear-cut questions scores well and detects nothing: the boundary rows are the ones that move when a rule changes.

## Verification

```bash
pytest labs/track-1-patterns/03-routing/tests -v
```

The route validation and misroute arithmetic run offline. Passing means an unknown label falls back to `other` instead of propagating, that `route_and_answer` reports which route it took, and that `misroute_rate` returns a fraction between 0 and 1 that matches a hand-counted example.

## Going further

- Route by model as well as by prompt: send the simplest route to a smaller model and measure the cost difference across the labelled set.
- Have the classifier return a confidence alongside the label and send anything below a threshold to `other`. Check whether the misroute rate improves.
- Inspect every misroute by hand. Most classifier failures are ambiguous route definitions, not model failures.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Routing: classifying an input and dispatching to a specialized follow-on call.
- **Databricks Generative AI Engineer Associate**: Problem decomposition and solution design; evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: Prompt engineering; experimentation; data analysis and visualization.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
