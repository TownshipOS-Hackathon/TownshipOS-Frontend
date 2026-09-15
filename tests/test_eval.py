from eval.run_triage_eval import metrics


def test_metrics_precision_recall_f1_and_emergency_recall():
    gold = [{"category": "lift", "urgency": "emergency"}, {"category": "lift", "urgency": "high"},
            {"category": "plumbing", "urgency": "medium"}, {"category": "other", "urgency": "low"}]
    pred = [{"category": "lift", "urgency": "high"}, {"category": "lift", "urgency": "high"},
            {"category": "lift", "urgency": "medium"}, {"category": "other", "urgency": "low"}]
    mt = metrics(gold, pred)
    assert mt["per_category"]["lift"] == {"precision": 2 / 3, "recall": 1.0, "f1": 0.8, "support": 2}
    assert mt["per_category"]["plumbing"]["recall"] == 0.0
    assert mt["urgency_accuracy"] == 0.75
    assert mt["emergency_recall"] == 0.0
    assert 0 < mt["macro_f1"] < 1
