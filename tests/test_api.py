import pytest
from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_root_health():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Drik Panchanga API. Use /panchanga with query params."}


def test_panchanga_endpoint_hyderabad_example():
    params = {
        "year": 2025,
        "month": 11,
        "day": 30,
        "latitude": 17.3850,
        "longitude": 78.4867,
        "tz_offset_hours": 5.5,
    }
    resp = client.get("/panchanga", params=params)
    assert resp.status_code == 200

    payload = resp.json()
    assert payload["input"]["date"] == "2025-11-30"
    panchanga = payload["panchanga"]

    assert panchanga["sun_moon"]["sunrise"] == "06:30:25"
    assert panchanga["sun_moon"]["sunset"] == "17:38:54"
    assert panchanga["sun_moon"]["moonrise"] == "13:48:21"
    assert panchanga["sun_moon"]["moonset"] == "01:25:45"
    assert panchanga["sun_moon"]["day_duration_hours"] == pytest.approx(11.141342561692, rel=1e-6)

    assert panchanga["angams"]["tithi"] == {
        "current_number": 10,
        "current_ends_at": "21:29:43",
    }
    assert panchanga["angams"]["nakshatra"] == {
        "current_number": 26,
        "current_ends_at": "25:10:54",
    }
    assert panchanga["angams"]["yoga"] == {
        "current_number": 15,
        "current_ends_at": "07:12:10",
        "leap_number": 16,
        "leap_ends_at": "28:21:50",
    }
    assert panchanga["angams"]["karana_numbers"] == [20]
    assert panchanga["angams"]["vaara_number"] == 0

    assert panchanga["month_year"] == {
        "masa_number": 9,
        "is_adhika_masa": False,
        "ritu_number": 4,
        "samvatsara_number": 39,
    }


def test_panchanga_invalid_date_returns_400():
    resp = client.get(
        "/panchanga",
        params={
            "year": 2025,
            "month": 2,
            "day": 30,  # invalid date
            "latitude": 17.3850,
            "longitude": 78.4867,
            "tz_offset_hours": 5.5,
        },
    )
    assert resp.status_code == 400
    assert "day is out of range" in resp.json()["detail"]


def test_next_maasikam_uses_sunrise_tithi_match():
    params = {
        "death_year": 2024,
        "death_month": 1,
        "death_day": 15,
        "latitude": 17.3850,
        "longitude": 78.4867,
        "tz_offset_hours": 5.5,
    }
    resp = client.get("/next-maasikam", params=params)
    assert resp.status_code == 200

    payload = resp.json()
    assert payload["death"]["paksha"] == "Shukla"
    assert payload["death"]["tithi"]["current_number"] == 5
    assert payload["next_maasikam"]["date"] == "2024-03-13"
    assert payload["next_maasikam"]["paksha"] == "Shukla"
    assert payload["next_maasikam"]["tithi_in_paksha"] == 5


def test_next_samvatsareekam_annual_rule():
    params = {
        "death_year": 2024,
        "death_month": 1,
        "death_day": 15,
        "latitude": 17.3850,
        "longitude": 78.4867,
        "tz_offset_hours": 5.5,
    }
    resp = client.get("/next-samvatsareekam", params=params)
    assert resp.status_code == 200

    payload = resp.json()
    assert payload["death"]["paksha"] == "Shukla"
    assert payload["death"]["tithi"]["current_number"] == 5
    assert payload["next_samvatsareekam"]["date"] == "2024-12-06"
    assert payload["next_samvatsareekam"]["paksha"] == "Shukla"
    assert payload["next_samvatsareekam"]["tithi_in_paksha"] == 5
