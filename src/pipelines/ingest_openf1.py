from src.extract.openf1_extractor import OpenF1Extractor
from src.load.sqlserver_loader import SQLServerLoader

def ingest_openf1(year: int = 2024):
    extractor = OpenF1Extractor()
    loader = SQLServerLoader()

    # Sessions
    sessions = extractor.get_sessions(year)
    loader.write_df(sessions, "bronze_sessions")

    # Laps
    for session_key in sessions["session_key"].unique():
        laps = extractor.get_laps(session_key)
        loader.write_df(laps, "bronze_laps")

    # Drivers
    for session_key in sessions["session_key"].unique():
        drivers = extractor.get_drivers(session_key)
        loader.write_df(drivers, "bronze_drivers")

if __name__ == "__main__":
    ingest_openf1()