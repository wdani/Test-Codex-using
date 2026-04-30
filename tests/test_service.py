import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "custom_components/ha_context_explorer_next"

# create lightweight package shell so relative imports do not trigger integration __init__.py
pkg_name = "custom_components.ha_context_explorer_next"
if pkg_name not in sys.modules:
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [str(PACKAGE)]
    sys.modules[pkg_name] = pkg

for name in ["analysis", "exporter", "privacy", "service"]:
    path = PACKAGE / f"{name}.py"
    spec = spec_from_file_location(f"custom_components.ha_context_explorer_next.{name}", path)
    mod = module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

service = sys.modules["custom_components.ha_context_explorer_next.service"]


def _state(entity_id, state, attributes=None, name=""):
    return SimpleNamespace(entity_id=entity_id, state=state, attributes=attributes or {}, name=name)


def test_build_snapshot_payload_shape():
    payload = service.build_snapshot_payload([
        _state("sensor.temp", "20", {"unit_of_measurement": "°C"}),
        _state("sensor.door_battery", "19", name="Door Battery"),
    ])
    assert set(payload.keys()) == {"summary", "noise", "battery", "recommendations", "recorder_advice", "domain_health"}


def test_build_ai_export_payload_contains_sections():
    export = service.build_ai_export_payload([_state("sensor.temp", "20")])
    assert export["schema_version"] == "2.0.0"
    assert "summary" in export and "noise" in export and "battery" in export
    assert "recorder_advice" in export


def test_build_ideas_payload_has_multiple_ideas():
    ideas = service.build_ideas_payload()["ideas"]
    assert len(ideas) >= 5


def test_recorder_advice_contains_yaml_preview():
    payload = service.build_snapshot_payload([_state("sensor.a", "1", {"x": "y" * 5000})])
    advice = payload["recorder_advice"]
    assert "yaml_preview" in advice
    assert "recorder" in advice["yaml_preview"]


def test_export_contains_action_queue_and_llm_context():
    export = service.build_ai_export_payload([_state("sensor.temp", "20")])
    assert "action_queue" in export
    assert "llm_context_short" in export
    assert "llm_context_deep" in export


def test_export_short_level_is_compact():
    export = service.build_ai_export_payload([_state("sensor.temp", "20")], level="short")
    assert export["export_level"] == "short"
    assert "llm_context_short" in export
    assert "llm_context_deep" not in export


def test_export_unknown_level_falls_back_to_deep():
    export = service.build_ai_export_payload([_state("sensor.temp", "20")], level="unknown")
    assert export["export_level"] == "deep"
    assert "llm_context_deep" in export


def test_domain_health_present_in_snapshot():
    payload = service.build_snapshot_payload([_state("sensor.temp", "20")])
    assert "domain_health" in payload
    assert isinstance(payload["domain_health"], list)
