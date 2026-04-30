from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "custom_components/ha_context_explorer_next/privacy.py"
spec = spec_from_file_location("privacy", MODULE_PATH)
privacy = module_from_spec(spec)
spec.loader.exec_module(privacy)


def test_stable_mask_is_deterministic():
    assert privacy.stable_mask("192.168.0.12", "ip") == privacy.stable_mask("192.168.0.12", "ip")


def test_mask_text_masks_ipv4_and_mac():
    masked = privacy.mask_text("Device at 192.168.1.10 with mac AA:BB:CC:DD:EE:FF")
    assert "192.168.1.10" not in masked
    assert "AA:BB:CC:DD:EE:FF" not in masked
    assert "ip_" in masked and "mac_" in masked


def test_mask_payload_masks_nested_strings():
    payload = {"x": ["mac AA:BB:CC:DD:EE:FF", {"ip": "10.0.0.1"}]}
    masked = privacy.mask_payload(payload)
    assert "AA:BB:CC:DD:EE:FF" not in str(masked)
    assert "10.0.0.1" not in str(masked)
