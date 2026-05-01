from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = Path(__file__).resolve().parents[1] / "custom_components/ha_context_explorer_next/analysis.py"
spec = spec_from_file_location("analysis", MODULE_PATH)
analysis = module_from_spec(spec)
spec.loader.exec_module(analysis)


def _state(entity_id, state, attributes=None, name=""):
    return SimpleNamespace(entity_id=entity_id, state=state, attributes=attributes or {}, name=name)


def test_build_entity_activity_summary_counts_domains_and_unavailable():
    states = [_state("sensor.temp", "20"), _state("light.kitchen", "on"), _state("light.hall", "unavailable")]
    summary = analysis.build_entity_activity_summary(states)
    assert summary["entities_total"] == 3
    assert summary["entities_unavailable_or_unknown"] == 1
    assert any(d["domain"] == "light" and d["count"] == 2 for d in summary["top_domains"])


def test_build_noise_summary_orders_by_score_desc():
    states = [_state("sensor.small", "1", {"a": "b"}), _state("sensor.big", "1", {"x": "y" * 50, "foo": "bar"})]
    top = analysis.build_noise_summary(states)["top_noisy_entities"]
    assert top[0]["entity_id"] == "sensor.big"


def test_build_battery_summary_detects_low_battery():
    states = [_state("sensor.door_battery", "15", name="Door Battery"), _state("sensor.remote_battery", "85", name="Remote Battery")]
    battery = analysis.build_battery_summary(states)
    assert battery["battery_entities_total"] == 2
    assert battery["battery_entities_low"] == 1


def test_generate_recommendations_returns_expected_items():
    summary = {"entities_total": 600, "entities_unavailable_or_unknown": 3}
    noise = {"top_noisy_entities": [{"entity_id": "sensor.big", "noise_score": 5000}]}
    battery = {"battery_entities_low": 1}
    rec_ids = {r["id"] for r in analysis.generate_recommendations(summary, noise, battery)}
    assert {"availability-review", "scale-recorder-review", "battery-attention", "noise-hotspots"}.issubset(rec_ids)


def test_generate_recommendations_sorted_by_severity_and_next_action():
    summary = {"entities_total": 10, "entities_unavailable_or_unknown": 1}
    noise = {"top_noisy_entities": [{"entity_id": "sensor.big", "noise_score": 3000}]}
    battery = {"battery_entities_low": 1}
    recs = analysis.generate_recommendations(summary, noise, battery)
    severities = [r["severity"] for r in recs]
    assert severities[0] == "high"
    assert all("next_action" in r for r in recs)


def test_generate_recommendations_noise_only_when_score_high():
    summary = {"entities_total": 10, "entities_unavailable_or_unknown": 0}
    battery = {"battery_entities_low": 0}
    low_noise = {"top_noisy_entities": [{"noise_score": 50}]}
    recs_low = analysis.generate_recommendations(summary, low_noise, battery)
    assert all(r["id"] != "noise-hotspots" for r in recs_low)

    high_noise = {"top_noisy_entities": [{"noise_score": 5000}]}
    recs_high = analysis.generate_recommendations(summary, high_noise, battery)
    assert any(r["id"] == "noise-hotspots" for r in recs_high)


def test_recommendation_includes_category_and_confidence():
    summary = {"entities_total": 600, "entities_unavailable_or_unknown": 3}
    noise = {"top_noisy_entities": [{"noise_score": 4000}]}
    battery = {"battery_entities_low": 1}
    recs = analysis.generate_recommendations(summary, noise, battery)
    assert all("category" in r and "confidence" in r for r in recs)


def test_domain_health_uses_noise_summary_without_attribute_rescan():
    class StateNoAttrs:
        def __init__(self, entity_id: str):
            self.entity_id = entity_id

        @property
        def attributes(self):
            raise AssertionError("attributes should not be read by build_domain_health")

    states = [StateNoAttrs("sensor.a"), StateNoAttrs("sensor.b"), StateNoAttrs("switch.c")]
    noise_summary = {"domain_noise_all": {"sensor": 1200, "switch": 300}}

    rows = analysis.build_domain_health(states, noise_summary)
    by_domain = {row["domain"]: row for row in rows}
    assert by_domain["sensor"]["noise_score"] == 1200
    assert by_domain["switch"]["noise_score"] == 300


def test_recorder_volume_summary_orders_hotspots_and_candidates():
    states = [
        _state("sensor.big_payload", "20", {"blob": "x" * 9000, "extra": "y" * 2000}),
        _state("lock.front", "locked", {"friendly_name": "Front Lock", "blob": "x" * 9000}),
        _state("light.kitchen", "on", {"brightness": 200}),
    ]
    noise = analysis.build_noise_summary(states)
    volume = analysis.build_recorder_volume_summary(states, noise)
    assert volume["totals"]["entities_scanned"] == 3
    assert volume["totals"]["high_impact_entities"] >= 1
    assert volume["top_entities"][0]["entity_id"] in {"sensor.big_payload", "lock.front"}
    assert "sensor.big_payload" in volume["safe_exclusion_candidates"]
    assert "lock.front" not in volume["safe_exclusion_candidates"]


def test_generate_recommendations_includes_recorder_volume_hotspots():
    summary = {"entities_total": 10, "entities_unavailable_or_unknown": 0}
    noise = {"top_noisy_entities": [{"noise_score": 50}]}
    battery = {"battery_entities_low": 0}
    recorder_volume = {"totals": {"high_impact_entities": 1, "domains_review": 0}}
    rec_ids = {r["id"] for r in analysis.generate_recommendations(summary, noise, battery, recorder_volume)}
    assert "recorder-volume-hotspots" in rec_ids
