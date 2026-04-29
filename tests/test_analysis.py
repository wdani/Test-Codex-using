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
    noise = {"top_noisy_entities": [{"entity_id": "sensor.big"}]}
    battery = {"battery_entities_low": 1}
    rec_ids = {r["id"] for r in analysis.generate_recommendations(summary, noise, battery)}
    assert {"availability-review", "scale-recorder-review", "battery-attention", "noise-hotspots"}.issubset(rec_ids)
