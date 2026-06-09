import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

# Colors derived from actual IDR663 128km product (17-entry indexed palette)
# (R, G, B, A) -> (intensity_label, mm_hr_midpoint)
COLOR_SCALE: dict[tuple[int, int, int, int], tuple[str, float | None]] = {
    (0, 0, 0, 0):           ("no_data",          None),
    (245, 245, 255, 255):   ("no_echo",           0.0),
    (192, 192, 192, 255):   ("range_ring",        None),
    (0, 0, 0, 255):         ("overlay",           None),
    (180, 180, 255, 255):   ("trace",             0.1),
    (120, 120, 255, 255):   ("light",             0.5),
    (20, 20, 255, 255):     ("light_moderate",    2.5),
    (0, 216, 195, 255):     ("moderate",          7.5),
    (0, 150, 144, 255):     ("moderate_heavy",    15.0),
    (0, 102, 102, 255):     ("heavy",             27.0),
    (255, 255, 0, 255):     ("very_heavy",        42.0),
    (255, 200, 0, 255):     ("intense",           60.0),
    (255, 150, 0, 255):     ("intense_plus",      85.0),
    (255, 100, 0, 255):     ("extreme",           125.0),
    (255, 0, 0, 255):       ("extreme_plus",      175.0),
    (200, 0, 0, 255):       ("catastrophic",      225.0),
    (120, 0, 0, 255):       ("catastrophic_plus", 300.0),
}

_TIMESTAMP_RE = re.compile(r"\.T\.(\d{12})\.png$")
_SKIP_LABELS = {"no_data", "range_ring", "overlay"}

_INTENSITY_RANK = [
    "no_echo", "trace", "light", "light_moderate", "moderate",
    "moderate_heavy", "heavy", "very_heavy", "intense", "intense_plus",
    "extreme", "extreme_plus", "catastrophic", "catastrophic_plus",
]
_RANK = {label: i for i, label in enumerate(_INTENSITY_RANK)}

# Thresholds (upper bound in mm/hr) for each intensity label
_MM_THRESHOLDS = [
    (0.0,   "no_echo"),
    (0.2,   "trace"),
    (1.0,   "light"),
    (5.0,   "light_moderate"),
    (10.0,  "moderate"),
    (20.0,  "moderate_heavy"),
    (35.0,  "heavy"),
    (50.0,  "very_heavy"),
    (70.0,  "intense"),
    (100.0, "intense_plus"),
    (150.0, "extreme"),
    (175.0, "extreme_plus"),
    (225.0, "catastrophic"),
    (float("inf"), "catastrophic_plus"),
]


def mmhr_to_label(mm_hr: float) -> str:
    for threshold, label in _MM_THRESHOLDS:
        if mm_hr <= threshold:
            return label
    return "catastrophic_plus"


def parse_timestamp(path: Path) -> datetime:
    m = _TIMESTAMP_RE.search(str(path))
    if not m:
        raise ValueError(f"Cannot parse timestamp from {path.name}")
    return datetime.strptime(m.group(1), "%Y%m%d%H%M").replace(tzinfo=timezone.utc)


def latlon_to_pixel(lat: float, lon: float, station: dict) -> tuple[int, int]:
    """Convert a lat/lon coordinate to pixel (x, y) in a 512x512 radar image."""
    km_per_px = station["range_km"] / 256
    cos_lat = math.cos(math.radians(station["lat"]))
    d_lat_km = (lat - station["lat"]) * 111.0
    d_lon_km = (lon - station["lon"]) * 111.0 * cos_lat
    px = int(256 + d_lon_km / km_per_px)
    py = int(256 - d_lat_km / km_per_px)  # y increases downward in image coords
    return px, py


def sample_location(
    pixels: np.ndarray, px: int, py: int, box: int = 5
) -> dict:
    """Sample rainfall at a pixel location using a box average."""
    half = box // 2
    region = pixels[
        max(0, py - half) : min(512, py + half + 1),
        max(0, px - half) : min(512, px + half + 1),
    ]

    rain_mm: list[float] = []    # mm/hr from pixels that actually have precipitation
    seen_labels: list[str] = []

    for row in region:
        for p in row:
            key = (int(p[0]), int(p[1]), int(p[2]), int(p[3]))
            label, mm_hr = COLOR_SCALE.get(key, ("unknown", None))
            if label in _SKIP_LABELS or label == "unknown":
                continue
            seen_labels.append(label)
            # Only include in average if it's actual rain (not no_echo = 0.0)
            if mm_hr is not None and label != "no_echo":
                rain_mm.append(mm_hr)

    if not seen_labels:
        return {"mm_hr": None, "intensity": "no_data", "pixel": (px, py)}

    avg_mm = round(float(np.mean(rain_mm)), 1) if rain_mm else 0.0

    # Label derived from average mm/hr (consistent with value)
    # Peak captures the highest single-pixel intensity in the box
    rain_labels = [l for l in seen_labels if l != "no_echo"]
    peak = max(rain_labels, key=lambda l: _RANK.get(l, 0)) if rain_labels else "no_echo"
    intensity = mmhr_to_label(avg_mm)

    return {"mm_hr": avg_mm, "intensity": intensity, "peak_intensity": peak, "pixel": (px, py)}


def analyze_frame(
    image_path: Path,
    locations: dict[str, tuple[float, float]],
    station: dict,
) -> dict:
    """Analyze a single radar frame for all named locations."""
    img = Image.open(image_path).convert("RGBA")
    pixels = np.array(img)
    ts = parse_timestamp(image_path)

    return {
        "timestamp": ts.isoformat(),
        "station": station["name"],
        "locations": {
            name: sample_location(pixels, *latlon_to_pixel(lat, lon, station))
            for name, (lat, lon) in locations.items()
        },
    }
