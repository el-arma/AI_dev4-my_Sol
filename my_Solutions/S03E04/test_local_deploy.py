"""
Smoke + domain tests for the S03E04-tool deployment.
Requires the service running at localhost:8001 (docker-compose up or uvicorn).

Ground truth from main.db (5 349 stock rows):
  Antena Bluetooth 2.4 GHz PCB  [PYERTD]  → Bydgoszcz, Krakow
  Bezpiecznik SMD 1 A           [KP84I9]  → Kielce, Zielona Gora
  Shared by Gdansk & Katowice             → Rezystor metalizowany 2.2 ohm 0.125 W 2% [TJXNKC]
                                            Tranzystor NPN 2N2222 TO-18 [9IV11V]
                                            Tranzystor PNP 2N2907 TO-18 [SDJQCO]
"""

import unicodedata
import pytest
import requests

BASE_URL = "http://localhost:8001"
ENDPOINT = f"{BASE_URL}/api/v1/S03E04-tool"


def post(params: str) -> requests.Response:
    return requests.post(ENDPOINT, json={"params": params}, timeout=60)


def strip_diacritics(text: str) -> str:
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()


def city_in_output(city: str, output: str) -> bool:
    """Match city name ignoring Polish diacritics (DB stores 'Krakow', LLM says 'Kraków')."""
    return strip_diacritics(city).lower() in strip_diacritics(output).lower()


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

def test_endpoint_reachable():
    r = post("test")
    assert r.status_code == 200


def test_response_contract():
    r = post("W jakich miastach sprzedawana jest Antena Bluetooth 2.4 GHz PCB?")
    assert r.status_code == 200
    body = r.json()
    assert "output" in body
    assert isinstance(body["output"], str)
    assert len(body["output"]) > 0


def test_output_fits_limit():
    r = post("W jakich miastach sprzedawana jest Antena Bluetooth 2.4 GHz PCB?")
    body = r.json()
    assert len(body["output"]) <= 490


# ---------------------------------------------------------------------------
# Domain — single item
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("city", ["Bydgoszcz", "Krakow"])
def test_antena_bluetooth_correct_cities(city: str):
    """All three cities stocking Antena Bluetooth should appear in the answer."""
    r = post("W jakich miastach sprzedawana jest Antena Bluetooth 2.4 GHz PCB?")
    assert r.status_code == 200
    output = r.json()["output"]
    assert city_in_output(city, output), f"Expected '{city}' (or with diacritics) in output, got: {output!r}"


@pytest.mark.parametrize("city", ["Kielce", "Zielona Gora"])
def test_bezpiecznik_smd_1a_correct_cities(city: str):
    """Both cities stocking Bezpiecznik SMD 1 A should appear in the answer."""
    r = post("W jakich miastach można kupić Bezpiecznik SMD 1 A?")
    assert r.status_code == 200
    output = r.json()["output"]
    assert city_in_output(city, output), f"Expected '{city}' (or with diacritics) in output, got: {output!r}"


# ---------------------------------------------------------------------------
# Domain — multi-item intersection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("city", ["Gdansk", "Katowice"])
def test_cities_with_tranzystor_npn_and_pnp(city: str):
    """Gdansk and Katowice both carry Tranzystor NPN 2N2222 [9IV11V] and PNP 2N2907 [SDJQCO].
    Query uses item codes so the agent can call find_cities_with_all_items directly.
    """
    r = post("Które miasta mają jednocześnie na stanie produkty o kodach 9IV11V i SDJQCO?")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
    output = r.json()["output"]
    assert city_in_output(city, output), f"Expected '{city}' (or with diacritics) in output, got: {output!r}"


# ---------------------------------------------------------------------------
# Domain — negative / graceful handling
# ---------------------------------------------------------------------------

def test_nonexistent_item_does_not_crash():
    r = post("W jakich miastach sprzedawany jest xyzzy_nonexistent_item_123?")
    assert r.status_code == 200
    body = r.json()
    assert "output" in body
