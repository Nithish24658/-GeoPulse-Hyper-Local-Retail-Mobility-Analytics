"""Generate reproducible synthetic GPS pings for GeoPulse."""
from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIELDNAMES = ["device_id", "latitude", "longitude", "event_timestamp"]
CITY_BOUNDS = {"min_latitude": 12.85, "max_latitude": 13.15,
               "min_longitude": 77.45, "max_longitude": 77.75}
SYNTHETIC_HUBS = [(12.9750, 77.6060), (12.9350, 77.6240),
                  (12.9780, 77.6400), (13.0280, 77.5400)]


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("start_time must include timezone information")
    return parsed.astimezone(timezone.utc)


def generate_records(device_count: int = 100, pings_per_device: int = 10,
                     seed: int = 42, start_time: datetime | None = None,
                     interval_minutes: int = 10) -> list[dict[str, str | float]]:
    """Create synthetic movement points using a seeded random walk."""
    if device_count < 1 or pings_per_device < 1 or interval_minutes < 1:
        raise ValueError("device_count, pings_per_device and interval_minutes must be at least 1")
    start = start_time or datetime(2026, 11, 10, tzinfo=timezone.utc)
    if start.tzinfo is None:
        raise ValueError("start_time must be timezone-aware")

    rng = random.Random(seed)
    records = []
    for device_number in range(1, device_count + 1):
        hub_lat, hub_lon = rng.choice(SYNTHETIC_HUBS)
        latitude = hub_lat + rng.uniform(-0.003, 0.003)
        longitude = hub_lon + rng.uniform(-0.003, 0.003)
        for ping_number in range(pings_per_device):
            if ping_number:
                latitude += rng.uniform(-0.0015, 0.0015)
                longitude += rng.uniform(-0.0015, 0.0015)
            latitude = min(max(latitude, CITY_BOUNDS["min_latitude"]), CITY_BOUNDS["max_latitude"])
            longitude = min(max(longitude, CITY_BOUNDS["min_longitude"]), CITY_BOUNDS["max_longitude"])
            event_time = start.astimezone(timezone.utc) + timedelta(minutes=interval_minutes * ping_number)
            records.append({
                "device_id": f"DEV{device_number:06d}",
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "event_timestamp": event_time.isoformat().replace("+00:00", "Z"),
            })
    return records


def validate_records(records: list[dict[str, str | float]]) -> None:
    for row_number, record in enumerate(records, start=1):
        if any(record.get(field) in (None, "") for field in FIELDNAMES):
            raise ValueError(f"Row {row_number} has a missing required field")
        latitude, longitude = float(record["latitude"]), float(record["longitude"])
        if not -90 <= latitude <= 90:
            raise ValueError(f"Row {row_number} has invalid latitude: {latitude}")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Row {row_number} has invalid longitude: {longitude}")
        timestamp = datetime.fromisoformat(str(record["event_timestamp"]).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError(f"Row {row_number} timestamp must include timezone information")


def write_csv(records: list[dict[str, str | float]], output_path: Path) -> None:
    validate_records(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic GeoPulse GPS ping data.")
    parser.add_argument("--devices", type=int, default=100)
    parser.add_argument("--pings-per-device", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start-time", default="2026-11-10T09:00:00Z")
    parser.add_argument("--interval-minutes", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("data/generated/gps_pings.csv"))
    args = parser.parse_args()
    records = generate_records(args.devices, args.pings_per_device, args.seed,
                               parse_timestamp(args.start_time), args.interval_minutes)
    write_csv(records, args.output)
    print(f"Generated {len(records):,} synthetic GPS pings at {args.output}")


if __name__ == "__main__":
    main()
