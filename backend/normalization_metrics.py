"""Paired development metrics with explicit abstentions and family grouping."""
from collections import Counter
import math
import numpy as np

PRIMARY = ["labor", "consumer", "mixed", "out_of_scope"]
SCOPE = ["fully_supported", "partially_supported", "unsupported"]


def ratio(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def assess(case, packet):
    expected = case["source_case"]
    result = packet.get("result")
    route = result["routing"] if result else {}
    # An explicit wording clarification is a system abstention, never a label.
    normalization = packet.get("normalization")
    action = route["routing_action"] if result else "clarify" if normalization and normalization["effective_question_text"] is None else "error"
    domains = sorted({c["allowed_domain"] for c in result["components"]}) if result else []
    components = result["components"] if result else []
    labeled = expected["expected_primary"] is not None
    primary = route.get("predicted_primary", "__abstain__")
    scope = route.get("predicted_scope", "__abstain__")
    primary_ok = primary == expected["expected_primary"] if labeled else None
    scope_ok = scope == expected["expected_scope"] if labeled else None
    route_ok = action == expected["expected_route"]
    domain_ok = domains == sorted(set(expected["expected_domains"]))
    relevant = []
    groups = []
    if expected["relevant_ids"]:
        groups.append((None, expected["relevant_ids"]))
    for concern in expected["concerns"]:
        if concern["domain"] != "excluded" and concern["relevant_ids"]:
            groups.append((concern["domain"], concern["relevant_ids"]))
    for domain, ids in groups:
        hits = [(rank, h["provision_id"]) for c in components if domain is None or c["allowed_domain"] == domain
                for rank, h in enumerate(c["candidates"][:5], 1) if h["provision_id"] in ids]
        relevant.append({"domain": domain, "hit_at_1": any(rank == 1 for rank, _ in hits),
                         "hit_at_5": bool(hits), "mrr_at_5": 1 / min(rank for rank, _ in hits) if hits else 0,
                         "known_relevant_recall_at_5": len({pid for _, pid in hits}) / len(set(ids))})
    candidate_count = sum(len(c["candidates"]) for c in components)
    negative_ok = candidate_count == 0 if expected["retrieval_judgment"] == "no_candidates" else None
    issues = []
    if primary_ok is False: issues.append("primary_label_mismatch_or_abstention")
    if scope_ok is False: issues.append("scope_label_mismatch_or_abstention")
    if not route_ok: issues.append("routing_mismatch")
    if not domain_ok: issues.append("supported_domain_coverage_mismatch")
    if relevant and not all(r["hit_at_5"] for r in relevant): issues.append("known_relevant_provision_missed")
    if negative_ok is False: issues.append("negative_candidate_leak")
    return {"labeled": labeled, "predicted_primary": primary, "predicted_scope": scope,
            "primary_correct": primary_ok, "scope_correct": scope_ok, "route": action,
            "route_correct": route_ok, "domain_correct": domain_ok,
            "retrieval": relevant, "candidate_count": candidate_count,
            "negative_control_correct": negative_ok, "issues": issues}


def head(rows, path, name, labels):
    eligible = [r for r in rows if r["case"]["source_case"]["expected_" + name] is not None]
    columns = labels + ["__abstain__"]
    matrix = [[0 for _ in columns] for _ in labels]
    for row in eligible:
        target = row["case"]["source_case"]["expected_" + name]
        predicted = row[path]["assessment"]["predicted_" + name]
        matrix[labels.index(target)][columns.index(predicted)] += 1
    classes = {}
    for i, label in enumerate(labels):
        tp, support = matrix[i][i], sum(matrix[i])
        predicted = sum(row[i] for row in matrix)
        classes[label] = {"support": support, "predicted_count": predicted,
                          "precision": tp / predicted if predicted else 0.0,
                          "recall": tp / support if support else None,
                          "f1": 2 * tp / (support + predicted) if support + predicted else None}
    f1s = [c["f1"] for c in classes.values() if c["support"]]
    correct = sum(matrix[i][i] for i in range(len(labels)))
    confidences = []
    for row in eligible:
        actual = row[path]["packet"]["result"]
        if actual:
            value = actual["routing"][name + "_confidence"]
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Invalid model confidence")
            confidences.append((value, row[path]["assessment"][name + "_correct"]))
    bins = []
    for i in range(10):
        values = [(c, ok) for c, ok in confidences if min(int(c * 10), 9) == i]
        bins.append({"lower": i / 10, "upper": (i + 1) / 10, "count": len(values),
                     "mean_label_confidence": float(np.mean([v[0] for v in values])) if values else None,
                     "observed_label_accuracy": float(np.mean([v[1] for v in values])) if values else None})
    ece = sum(b["count"] * abs(b["mean_label_confidence"] - b["observed_label_accuracy"])
              for b in bins if b["count"]) / len(confidences) if confidences else None
    return {"accuracy": ratio(correct, len(eligible)), "macro_f1": float(np.mean(f1s)) if f1s else None,
            "per_class": classes, "confusion": {"true_rows": labels, "predicted_columns": columns, "counts": matrix},
            "abstentions": sum(row[-1] for row in matrix),
            "confidence_calibration": {"prediction_count": len(confidences), "ece": ece, "bins": bins,
                                       "note": "Only available label predictions; abstentions have no fabricated probability. Not legal correctness."}}


def summarize_path(rows, path):
    assessments = [r[path]["assessment"] for r in rows]
    relevant = [item for a in assessments for item in a["retrieval"]]
    negatives = [a for a in assessments if a["negative_control_correct"] is not None]
    clarification = [r for r in rows if r["case"]["source_case"]["expected_route"] == "clarify"]
    unsupported = [r for r in rows if r["case"]["source_case"]["expected_scope"] == "unsupported"]
    ms = [r[path]["packet"]["total_query_ms"] for r in rows]
    primary, scope = head(rows, path, "primary", PRIMARY), head(rows, path, "scope", SCOPE)
    return {"inputs": len(rows), "families": len({r["case"]["family_id"] for r in rows}),
            "primary": primary, "scope": scope,
            "partial_support_recall": scope["per_class"]["partially_supported"]["recall"],
            "out_of_scope_recall": primary["per_class"]["out_of_scope"]["recall"],
            "route_match": ratio(sum(a["route_correct"] for a in assessments), len(rows)),
            "domain_match": ratio(sum(a["domain_correct"] for a in assessments), len(rows)),
            "clarification_success": ratio(sum(r[path]["assessment"]["route_correct"] for r in clarification), len(clarification)),
            "unsupported_admission": ratio(sum(r[path]["assessment"]["route"].startswith("retrieve_") for r in unsupported), len(unsupported)),
            "known_relevant_hit_at_1": ratio(sum(r["hit_at_1"] for r in relevant), len(relevant)),
            "known_relevant_hit_at_5": ratio(sum(r["hit_at_5"] for r in relevant), len(relevant)),
            "known_relevant_mrr_at_5": ratio(sum(r["mrr_at_5"] for r in relevant), len(relevant)),
            "known_relevant_recall_at_5": ratio(sum(r["known_relevant_recall_at_5"] for r in relevant), len(relevant)),
            "negative_candidate_leakage": ratio(sum(not a["negative_control_correct"] for a in negatives), len(negatives)),
            "latency_ms": {"median": float(np.median(ms)), "p95": float(np.quantile(ms, .95))},
            "cases_with_issues": sum(bool(a["issues"]) for a in assessments),
            "issue_counts": dict(Counter(issue for a in assessments for issue in a["issues"]))}


def paired_interval(rows, metric, replicates=2000):
    groups = {}
    for row in rows:
        if metric in {"primary_correct", "scope_correct"} and not row["baseline"]["assessment"]["labeled"]:
            continue
        if metric == "retrieval_hit":
            a, b = row["baseline"]["assessment"]["retrieval"], row["normalized"]["assessment"]["retrieval"]
            if not a: continue
            n = sum(v["hit_at_5"] for v in b) - sum(v["hit_at_5"] for v in a)
            d = len(a)
        else:
            n = int(row["normalized"]["assessment"][metric]) - int(row["baseline"]["assessment"][metric])
            d = 1
        group = groups.setdefault(row["case"]["family_id"], [0, 0])
        group[0] += n
        group[1] += d
    if not groups:
        return {"difference": None, "family_cluster_bootstrap_95": None, "families": 0}
    values = np.array(list(groups.values()), dtype=float)
    rng = np.random.default_rng(20261019)
    samples = values[rng.integers(0, len(values), size=(replicates, len(values)))].sum(axis=1)
    rates = samples[:, 0] / samples[:, 1]
    return {"difference": float(values[:, 0].sum() / values[:, 1].sum()),
            "family_cluster_bootstrap_95": [float(x) for x in np.quantile(rates, [.025, .975])],
            "families": len(values), "denominator": int(values[:, 1].sum()),
            "note": "Paired family resampling preserves clear/noisy dependence. Descriptive development uncertainty; not population or independent accuracy."}


def summarize(rows, protocol, reviews=()):
    groups = {"all": rows, "clear": [r for r in rows if r["case"]["variation"] == "clear"],
              "noisy": [r for r in rows if r["case"]["variation"] == "noisy"]}
    metrics = {name: {path: summarize_path(group, path) for path in ["baseline", "normalized"]}
               for name, group in groups.items()}
    deltas = {name: {metric: paired_interval(group, metric) for metric in ["primary_correct", "scope_correct", "route_correct", "retrieval_hit"]}
              for name, group in groups.items()}
    normalizations = [r["normalized"]["packet"]["normalization"] for r in rows]
    called = [n for n in normalizations if n["llm_calls"]]
    usage_complete = all(all(type(n["usage"].get(k)) is int for k in ["input_tokens", "output_tokens"]) for n in called)
    input_tokens = sum(n["usage"].get("input_tokens", 0) for n in called)
    output_tokens = sum(n["usage"].get("output_tokens", 0) for n in called)
    prices = protocol["pricing_usd_per_million_tokens"]
    cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
    accepted_ids = {r["case"]["case_id"] for r in rows if r["normalized"]["packet"]["normalization"]["status"] == "applied"}
    review_by_id = {r["case_id"]: r for r in reviews}
    if len(review_by_id) != len(list(reviews)) or set(review_by_id) - accepted_ids:
        raise ValueError("Duplicate or non-accepted semantic review")
    verdicts = Counter(r["verdict"] for r in reviews)
    return {"version": protocol["version"], "role": "paired_synthetic_development_comparison",
            "counts": {"base_questions": len({r["case"]["base_case_id"] for r in rows}),
                       "input_forms": len(rows), "pipeline_executions": 2 * len(rows),
                       "independent_human_questions": 0},
            "strata": metrics, "paired_differences": deltas,
            "noise_profiles": {p: {path: summarize_path([r for r in rows if r["case"]["noise_profile"] == p], path)
                                    for path in ["baseline", "normalized"]}
                               for p in sorted({r["case"]["noise_profile"] for r in rows if r["case"]["noise_profile"]})},
            "normalization": {"status_counts": dict(Counter(n["status"] for n in normalizations)),
                              "validation_failure_counts": dict(Counter(n["validation_failure"] for n in normalizations if n.get("validation_failure"))),
                              "llm_requests": len(called),
                              "clear_llm_requests": sum(r["normalized"]["packet"]["normalization"]["llm_calls"] for r in groups["clear"]),
                              "noisy_llm_requests": sum(r["normalized"]["packet"]["normalization"]["llm_calls"] for r in groups["noisy"]),
                              "input_tokens": input_tokens, "output_tokens_including_reasoning": output_tokens,
                              "estimated_provider_cost_usd": cost, "usage_complete": usage_complete,
                              "cost_note": "Token-rate estimate, not an invoice. Failed requests without usage make this incomplete."},
            "semantic_review": {"role": "disclosed_Codex_AI_audit_not_independent_human_judgment",
                                "accepted_rewrites": len(accepted_ids), "reviewed": len(reviews),
                                "pending": len(accepted_ids - set(review_by_id)), "verdict_counts": dict(verdicts),
                                "AI_flagged_meaning_change_rate": ratio(verdicts["meaning_changed"], len(reviews)),
                                "uncertain_rate": ratio(verdicts["uncertain"], len(reviews)),
                                "independent_meaning_change_rate": None},
            "formal_acceptance_completed": False, "answer_generation_allowed": False, "deployment_allowed": False,
            "limitations": ["Reused AI-authored cases and synthetic perturbations; not independent human gold or real typing prevalence.",
                            "Noisy inputs inherit the intended source meaning. Correct clarification can be a safe deferral while reducing label accuracy.",
                            "Abstentions remain in labeled accuracy/recall denominators and confusion columns.",
                            "Known-relevant judgments are partial development judgments. Candidate availability alone is not relevance.",
                            "Semantic review is AI authored and may miss changes; rejected rewrites are not counted as observed meaning changes.",
                            "Timing includes current-guidance integrity checks and conditional API latency, excluding model startup.",
                            "This does not evaluate generated legal answers or approve current law."]}
