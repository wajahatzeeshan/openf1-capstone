from src.extract.openf1_extractor import OpenF1Extractor
from src.load.sqlserver_loader import SQLServerLoader


def ingest_openf1(year=None):
    extractor = OpenF1Extractor()
    loader = SQLServerLoader()

    # Determine years to ingest
    if year is None:
        all_sessions = extractor.get_sessions()

        if all_sessions.empty:
            raise RuntimeError("No sessions found in OpenF1 API; cannot determine latest year.")

        start = int(all_sessions["year"].min())   # oldest year
        end = int(all_sessions["year"].max())     # newest year
        year = list(range(start, end + 1))

    elif isinstance(year, int):
        year = [year]

    elif isinstance(year, tuple) and len(year) == 2:
        start, end = year
        year = list(range(start, end + 1))

    print(f"Starting OpenF1 ingestion for {year}")

    # -------------------------
    # Loop through each year
    # -------------------------
    for y in year:
        print(f"\nExtracting sessions for year {y}...")
        sessions = extractor.get_sessions(y)
        loader.write_df(sessions, "bronze_sessions")

        if sessions.empty:
            print(f"No sessions found for year {y}, skipping.")
            continue

        session_keys = sessions["session_key"].unique()

        # -------------------------
        # Loop through each session
        # -------------------------
        for session_key in session_keys:
            session_key = int(session_key)
            
            if loader.is_session_loaded(session_key):
                print(f"Session {session_key} already ingested. Skipping.")
                continue
            
            print(f"\nProcessing session {session_key}")

            # Drivers
            print("  Extracting drivers...")
            drivers = extractor.get_drivers(session_key)
            loader.write_df(drivers, "bronze_drivers")

            # Laps
            print("  Extracting laps...")
            laps = extractor.get_laps(session_key)
            loader.write_df(laps, "bronze_laps")

            # Pit stops
            print("  Extracting pit stops...")
            pit = extractor.get_pit_stops(session_key)
            loader.write_df(pit, "bronze_pit_stops")

            # Weather
            print("  Extracting weather...")
            weather = extractor.get_weather(session_key)
            loader.write_df(weather, "bronze_weather")

            # Positions
            print("  Extracting positions...")
            positions = extractor.get_positions(session_key)
            loader.write_df(positions, "bronze_positions")

            # Telemetry (car data)
            print("  Extracting car telemetry...")
            if not drivers.empty and "driver_number" in drivers.columns:
                for driver_number in drivers["driver_number"].unique():
                    car_data = extractor.get_car_data(session_key, driver_number)
                    loader.write_df(car_data, "bronze_car_data")

    # Mark session as completed
            loader.mark_session_loaded(session_key)
            print(f"Session {session_key} marked as ingested.")
        
    print("\nIngestion complete.")
    loader.close()


if __name__ == "__main__":
    ingest_openf1()