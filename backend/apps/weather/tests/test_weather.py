import pytest
import responses

from apps.weather import client

RAW = {
    "timezone": "Africa/Casablanca",
    "current": {"time": "2026-11-24T19:00", "temperature_2m": 18.84, "relative_humidity_2m": 90,
                "wind_speed_10m": 3.3, "weather_code": 95},
    "hourly": {
        "time": [f"2026-11-24T{h:02d}:00" for h in range(24)] + [f"2026-11-25T{h:02d}:00" for h in range(24)],
        "temperature_2m": list(range(48)),
        "precipitation_probability": [10] * 48,
        "wind_speed_10m": [5.0] * 48,
        "weather_code": [3] * 48,
    },
    "daily": {"time": ["2026-11-24", "2026-11-25"], "weather_code": [95, 3],
              "temperature_2m_max": [21.4, 20.0], "temperature_2m_min": [14.2, 13.0]},
}


def test_normalize_forecast_starts_at_current_hour():
    out = client.normalize_forecast(RAW)
    assert out["current"]["temp_c"] == 18.8
    assert out["current"]["label"] == "Orages"
    assert out["current"]["precip_prob"] == 10
    assert out["hourly"][0]["time"] == "2026-11-24T19:00"
    assert len(out["hourly"]) == 9  # 24 h, un point toutes les 3 h
    assert out["daily"][0] == {"date": "2026-11-24", "code": 95, "temp_max_c": 21.0, "temp_min_c": 14.0}


@pytest.mark.django_db
class TestWeatherEndpoint:
    @responses.activate
    def test_by_coordinates_cached(self, api_client):
        responses.add(responses.GET, client.FORECAST_URL, json=RAW, status=200)
        for _ in range(2):
            resp = api_client.get("/api/v1/weather/", {"latitude": 33.57, "longitude": -7.59, "city": "Casablanca"})
            assert resp.status_code == 200
            assert resp.data["location"]["name"] == "Casablanca"
        assert len(responses.calls) == 1

    @responses.activate
    def test_by_city_geocodes(self, api_client):
        responses.add(responses.GET, client.GEOCODING_URL, status=200, json={"results": [
            {"name": "Paris", "latitude": 48.85, "longitude": 2.35, "country": "France", "country_code": "FR"}]})
        responses.add(responses.GET, client.FORECAST_URL, json=RAW, status=200)
        resp = api_client.get("/api/v1/weather/", {"city": "Paris", "country": "France"})
        assert resp.status_code == 200
        assert resp.data["location"]["latitude"] == 48.85

    @responses.activate
    def test_unknown_city_404(self, api_client):
        responses.add(responses.GET, client.GEOCODING_URL, json={}, status=200)
        assert api_client.get("/api/v1/weather/", {"city": "Zzzz"}).status_code == 404

    def test_invalid_params(self, api_client):
        assert api_client.get("/api/v1/weather/").status_code == 400
        assert api_client.get("/api/v1/weather/", {"latitude": "x", "longitude": 1}).status_code == 400
        assert api_client.get("/api/v1/weather/", {"latitude": 99, "longitude": 1}).status_code == 400
