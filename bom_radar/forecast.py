import json
import os

import anthropic

_SYSTEM_PROMPT = """You are a practical weather analyst interpreting Bureau of Meteorology radar data for Australian locations.
You receive structured rainfall intensity data sampled every 5 minutes from BOM radar images.

Intensity categories (light to severe):
- no_echo / no_data: no precipitation
- trace: < 0.2 mm/hr
- light: 0.2–1 mm/hr
- light_moderate: 1–5 mm/hr
- moderate: 5–10 mm/hr
- moderate_heavy: 10–20 mm/hr
- heavy: 20–35 mm/hr
- very_heavy: 35–50 mm/hr (BOM heavy rain warning threshold)
- intense / extreme: 50–150+ mm/hr (severe weather)

Give practical, concise advice. Focus on trends and suburb-level differences."""


def generate_forecast(time_series: list[dict]) -> str:
    """Send radar time series to Claude and return a human-readable weather summary."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    summary = [
        {
            "time": frame["timestamp"],
            "readings": {
                name: f"{data['mm_hr']} mm/hr ({data['intensity']})"
                if data["mm_hr"] is not None
                else data["intensity"]
                for name, data in frame["locations"].items()
            },
        }
        for frame in time_series
    ]

    user_content = (
        f"Radar time series ({len(time_series)} frames, ~5 min intervals):\n\n"
        f"{json.dumps(summary, indent=2)}\n\n"
        "Please provide:\n"
        "1. **Current conditions** (1–2 sentences)\n"
        "2. **Trend** (moving in, moving out, intensifying, or clearing?)\n"
        "3. **Suburb outlook** (one line per location for the next 30 minutes)\n"
        "4. **Practical advice** (umbrella? windows? outdoor plans?)"
    )

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    return response.content[0].text
