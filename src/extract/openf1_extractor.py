import requests
import pandas as pd
from typing import Dict, Any, List

BASE_URL = "https://api.openf1.org/v1"

class OpenF1Extractor:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
         
    def _get(self, endpoint: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        """
        Internal helper to call the OpenF1 API.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.get(url, params=params or {})

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"OpenF1 API request failed: {e}")

        return response.json()

    def get_sessions(self, year: int | None = None) -> pd.DataFrame:
        """
        Fetch all sessions for a given year.
        """
        params = {}
        if year:
            params["year"] = year

        data = self._get("sessions", params)
        return pd.DataFrame(data)

    def get_laps(self, session_key: int) -> pd.DataFrame:
        """
        Fetch lap-by-lap timing for a session.
        """
        params = {"session_key": session_key}
        data = self._get("laps", params)
        return pd.DataFrame(data)

    def get_drivers(self, session_key: int) -> pd.DataFrame:
        """
        Fetch driver information for a session.
        """
        params = {"session_key": session_key}
        data = self._get("drivers", params)
        return pd.DataFrame(data)
    def get_pit_stops(self, session_key: int | None = None) -> pd.DataFrame:
        """
        Fetch pit stop events.
        """
        params = {}
        if session_key:
            params["session_key"] = session_key

        data = self._get("pit", params)
        return pd.DataFrame(data)

    def get_weather(self, session_key: int | None = None) -> pd.DataFrame:
        """
        Fetch weather data for a session.
        """
        params = {}
        if session_key:
            params["session_key"] = session_key

        data = self._get("weather", params)
        return pd.DataFrame(data)

    def get_positions(self, session_key: int) -> pd.DataFrame:
        """
        Fetch position data over time for a session.
        """
        params = {"session_key": session_key}
        data = self._get("position", params)
        return pd.DataFrame(data)

    def get_car_data(self, session_key: int, driver_number: int | None = None) -> pd.DataFrame:
        """
        Fetch car telemetry (speed, throttle, brake, gear, rpm, drs).
        """
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number

        data = self._get("car_data", params)
        return pd.DataFrame(data)

