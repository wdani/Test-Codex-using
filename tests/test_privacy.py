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


def test_mask_text_masks_email_and_ipv6():
    masked = privacy.mask_text("admin@example.com from fe80::1ff:fe23:4567:890a")
    assert "admin@example.com" not in masked
    assert "fe80::1ff:fe23:4567:890a" not in masked
    assert "email_" in masked and "ip6_" in masked


def test_mask_payload_masks_nested_strings():
    payload = {"x": ["mac AA:BB:CC:DD:EE:FF", {"ip": "10.0.0.1"}]}
    masked = privacy.mask_payload(payload)
    assert "AA:BB:CC:DD:EE:FF" not in str(masked)
    assert "10.0.0.1" not in str(masked)


def test_mask_payload_masks_sensitive_attribute_keys():
    payload = {
        "attributes": {
            "friendly_name": "Daniel Bedroom",
            "latitude": 47.3769,
            "longitude": 8.5417,
            "email": "daniel@example.com",
            "host": "homeassistant.local",
        }
    }
    masked = privacy.mask_payload(payload)
    masked_text = str(masked)
    assert "Daniel Bedroom" not in masked_text
    assert "47.3769" not in masked_text
    assert "8.5417" not in masked_text
    assert "daniel@example.com" not in masked_text
    assert "homeassistant.local" not in masked_text
    assert "identity_" in masked_text
    assert "location_" in masked_text
    assert "email_" in masked_text
    assert "network_" in masked_text


def test_mask_payload_preserves_exact_pattern_aliases_for_sensitive_keys():
    payload = {
        "email": "daniel@example.com",
        "ip_address": "192.168.1.10",
        "mac": "AA:BB:CC:DD:EE:FF",
    }
    masked = privacy.mask_payload(payload)
    assert masked["email"] == privacy.mask_text("daniel@example.com")
    assert masked["ip_address"] == privacy.mask_text("192.168.1.10")
    assert masked["mac"] == privacy.mask_text("AA:BB:CC:DD:EE:FF")


def test_privacy_status_does_not_expose_key(monkeypatch):
    monkeypatch.setenv("HCX_MASK_KEY", "super-secret-value")
    status = privacy.build_privacy_status()
    assert status["exports_enabled"] is True
    assert status["mask_key"] == "custom"
    assert "super-secret-value" not in str(status)
