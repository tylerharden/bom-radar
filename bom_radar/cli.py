import argparse
import json
import sys
import tempfile
from pathlib import Path

from .fetch import download_frames
from .forecast import generate_forecast
from .parse import analyze_frame
from .stations import PRESET_LOCATIONS, STATIONS


def _parse_location(s: str) -> tuple[str, float, float]:
    """Parse 'Name:lat,lon' into (name, lat, lon)."""
    try:
        name, coords = s.split(":", 1)
        lat, lon = coords.split(",", 1)
        return name.strip(), float(lat), float(lon)
    except (ValueError, IndexError):
        raise argparse.ArgumentTypeError(
            f"Invalid location format '{s}'. Expected 'Name:lat,lon'"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bom-radar",
        description="BOM weather radar analysis with AI forecast",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  bom-radar --preset gold-coast
  bom-radar --preset brisbane --frames 6
  bom-radar --location "My House:-28.05,153.4" --location "Work:-27.97,153.40"
  bom-radar --preset gold-coast --no-forecast --json
        """,
    )
    parser.add_argument(
        "--station",
        default="IDR663",
        choices=list(STATIONS.keys()),
        help="Radar station ID (default: IDR663 Brisbane/Gold Coast)",
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESET_LOCATIONS.keys()),
        help="Use a preset suburb group",
    )
    parser.add_argument(
        "--location",
        action="append",
        dest="locations",
        metavar="NAME:LAT,LON",
        type=_parse_location,
        help="Custom location — can repeat. Format: 'Suburb:-28.01,153.43'",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=12,
        metavar="N",
        help="Number of radar frames to fetch (default: 12, ~1 hour)",
    )
    parser.add_argument(
        "--no-forecast",
        action="store_true",
        help="Skip the AI forecast, print raw data only",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output raw time-series data as JSON",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "bom_radar_cache",
        help="Directory for cached radar images",
    )

    args = parser.parse_args()

    locations: dict[str, tuple[float, float]] = {}
    if args.preset:
        locations.update(PRESET_LOCATIONS[args.preset])
    if args.locations:
        for name, lat, lon in args.locations:
            locations[name] = (lat, lon)

    if not locations:
        parser.error("Specify at least one of --preset or --location")

    station = STATIONS[args.station]

    print(
        f"Fetching {args.frames} frames from {station['name']} radar...",
        file=sys.stderr,
    )
    frame_paths = download_frames(args.station, args.cache_dir, args.frames)
    print(f"  {len(frame_paths)} frames ready", file=sys.stderr)

    print("Analysing pixel data...", file=sys.stderr)
    time_series = [analyze_frame(p, locations, station) for p in frame_paths]

    if args.output_json:
        print(json.dumps(time_series, indent=2))
        return

    latest = time_series[-1]
    print(f"\nLatest snapshot — {latest['timestamp']} UTC")
    print(f"Station: {latest['station']}\n")
    for name, data in latest["locations"].items():
        if data["mm_hr"] is not None:
            peak = data.get("peak_intensity", data["intensity"])
            peak_note = f"  peak: {peak}" if peak != data["intensity"] else ""
            print(f"  {name:<24} {data['mm_hr']:>6.1f} mm/hr  ({data['intensity']}){peak_note}")
        else:
            print(f"  {name:<24}  {'—':>6}         ({data['intensity']})")

    if not args.no_forecast:
        print("\nGenerating AI forecast...\n", file=sys.stderr)
        try:
            forecast = generate_forecast(time_series)
            print("-" * 60)
            print(forecast)
            print("-" * 60)
        except ValueError as e:
            print(f"\n[Forecast skipped: {e}]", file=sys.stderr)
            print(
                "Set ANTHROPIC_API_KEY to enable AI forecasts.",
                file=sys.stderr,
            )
