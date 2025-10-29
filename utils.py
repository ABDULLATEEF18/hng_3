
# utils.py
import requests
import time
import random
import json
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

RESTCOUNTRIES_URL = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_URL = "https://open.er-api.com/v6/latest/USD"
REQUEST_TIMEOUT = 10  # seconds

def fetch_countries():
    try:
        r = requests.get(RESTCOUNTRIES_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise RuntimeError(f"restcountries_fetch_failed: {e}")

def fetch_exchange_rates():
    try:
        r = requests.get(EXCHANGE_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        # API returns structure with 'rates' usually
        rates = data.get("rates") or data.get("rates", {})
        if not rates:
            # some APIs use "conversion_rates" etc; try alternatives
            rates = data.get("conversion_rates") or data.get("rates", {})
        return rates
    except Exception as e:
        raise RuntimeError(f"exchange_fetch_failed: {e}")

def compute_estimated_gdp(population, exchange_rate):
    # random multiplier between 1000 and 2000
    if population is None:
        return None
    multiplier = random.uniform(1000, 2000)
    if exchange_rate is None or exchange_rate == 0:
        return None
    return (population * multiplier) / exchange_rate

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def generate_summary_image(total_countries, top5_list, last_refreshed_at, out_path="cache/summary.png"):
    """
    top5_list: list of tuples (name, estimated_gdp) sorted desc
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # image size & colors
    W, H = 1000, 600
    bg = (15, 23, 42)
    text_color = (240, 240, 240)

    img = Image.new("RGB", (W, H), color=bg)
    d = ImageDraw.Draw(img)

    try:
        font_b = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_s = ImageFont.truetype("DejaVuSans.ttf", 18)
    except Exception:
        font_b = ImageFont.load_default()
        font_s = ImageFont.load_default()

    # Header
    d.text((30, 20), "Country Cache Summary", font=font_b, fill=text_color)
    d.text((30, 60), f"Total countries: {total_countries}", font=font_s, fill=text_color)
    d.text((30, 90), f"Last refreshed: {last_refreshed_at}", font=font_s, fill=text_color)

    # Top 5 table
    d.text((30, 140), "Top 5 countries by estimated GDP", font=font_b, fill=text_color)
    y = 190
    for i, (name, gdp) in enumerate(top5_list, 1):
        gdp_str = f"${gdp:,.2f}" if gdp is not None else "N/A"
        d.text((40, y), f"{i}. {name}", font=font_s, fill=text_color)
        d.text((500, y), gdp_str, font=font_s, fill=text_color)
        y += 36

    img.save(out_path)
    return out_path
