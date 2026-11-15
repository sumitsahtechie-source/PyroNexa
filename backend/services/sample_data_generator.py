"""PyroNexa 26 - Scientific Sample Dataset Generator

Synthesizes high-fidelity active fire datasets modeled on empirical NASA FIRMS
observations across multiple biomes (Western US, Amazon, Mediterranean, Australia, SE Asia)
and multi-year historical periods (2021-2026).

Reflects empirical sensor characteristics:
- VIIRS 375m detects ~3.5x to 4.2x more active fire pixels than MODIS 1km for identical burning complexes.
- True biome-specific seasonal cycles (e.g. Northern Hemisphere summer vs Southern Hemisphere summer).
- Accurate FRP log-normal distributions and confidence values.
"""

from datetime import datetime, date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from backend.config import Config, PRESET_REGIONS
from backend.utils.geo_utils import get_grid_cell, estimate_pixel_footprint_km2


def generate_sample_dataset(output_path: Optional[Path] = None, seed: int = 42) -> pd.DataFrame:
    """Generate and save a multi-year harmonized sample dataset."""
    rng = np.random.RandomState(seed)
    records = []

    # Biome seasonal profiles: peak months (1-12) and baseline monthly activity weights
    biome_profiles = {
        "california": {
            "bbox": [-124.0, 33.0, -115.0, 41.5],
            "peak_months": [7, 8, 9, 10],  # Jul-Oct
            "month_weights": [0.05, 0.05, 0.1, 0.2, 0.3, 0.6, 1.2, 1.5, 1.3, 0.8, 0.3, 0.1],
            "cluster_centers": [(37.5, -119.5), (39.8, -121.2), (34.2, -118.4), (40.5, -122.5)],
            "base_events": 45
        },
        "amazon": {
            "bbox": [-70.0, -12.0, -50.0, -2.0],
            "peak_months": [8, 9, 10],  # Aug-Oct
            "month_weights": [0.1, 0.1, 0.15, 0.2, 0.3, 0.5, 0.9, 1.8, 1.9, 1.2, 0.4, 0.15],
            "cluster_centers": [(-8.5, -62.8), (-10.2, -55.4), (-4.5, -53.2), (-6.1, -58.9)],
            "base_events": 60
        },
        "mediterranean": {
            "bbox": [-8.0, 36.0, 25.0, 43.5],
            "peak_months": [6, 7, 8, 9],  # Jun-Sep
            "month_weights": [0.05, 0.05, 0.1, 0.2, 0.4, 1.1, 1.6, 1.7, 0.9, 0.3, 0.1, 0.05],
            "cluster_centers": [(39.5, -4.5), (38.2, 23.5), (40.3, 15.5), (37.5, -7.8)],
            "base_events": 35
        },
        "australia": {
            "bbox": [142.0, -38.0, 152.0, -30.0],
            "peak_months": [11, 12, 1, 2],  # Nov-Feb (Southern Hemisphere Summer)
            "month_weights": [1.4, 1.5, 0.8, 0.4, 0.2, 0.1, 0.1, 0.15, 0.3, 0.6, 1.1, 1.3],
            "cluster_centers": [(-34.5, 150.2), (-36.8, 148.5), (-31.2, 151.8), (-37.5, 146.2)],
            "base_events": 40
        },
        "southeast_asia": {
            "bbox": [98.0, -4.0, 116.0, 5.0],
            "peak_months": [8, 9, 10],  # Aug-Oct
            "month_weights": [0.2, 0.4, 0.6, 0.3, 0.2, 0.3, 0.5, 1.3, 1.6, 1.1, 0.3, 0.2],
            "cluster_centers": [(-1.5, 103.5), (-2.8, 112.5), (2.5, 101.5), (-3.2, 114.2)],
            "base_events": 35
        }
    }

    years = [2021, 2022, 2023, 2024, 2025, 2026]

    for biome_key, profile in biome_profiles.items():
        min_lon, min_lat, max_lon, max_lat = profile["bbox"]
        month_weights = profile["month_weights"]
        cluster_centers = profile["cluster_centers"]
        base_events = profile["base_events"]

        for year in years:
            # Year multiplier: incorporate historical climate anomaly variations
            # E.g. 2021 and 2023 were extreme fire years globally, 2024 moderate
            year_multipliers = {2021: 1.35, 2022: 0.95, 2023: 1.45, 2024: 1.1, 2025: 1.05, 2026: 1.25}
            y_mult = year_multipliers.get(year, 1.0)

            for month in range(1, 13):
                # For 2026, generate up to current month (Nov)
                if year == 2026 and month > 11:
                    continue

                m_weight = month_weights[month - 1]
                num_fire_clusters = int(rng.poisson(base_events * m_weight * y_mult * 0.15))
                num_fire_clusters = max(1, num_fire_clusters)

                days_in_month = 28 if month == 2 else (30 if month in (4, 6, 9, 11) else 31)

                for _ in range(num_fire_clusters):
                    # Pick a cluster center with some spatial jitter
                    center_lat, center_lon = cluster_centers[rng.randint(len(cluster_centers))]
                    fire_center_lat = np.clip(center_lat + rng.normal(0, 0.6), min_lat + 0.1, max_lat - 0.1)
                    fire_center_lon = np.clip(center_lon + rng.normal(0, 0.6), min_lon + 0.1, max_lon - 0.1)

                    day_of_month = rng.randint(1, days_in_month + 1)
                    acq_date = f"{year}-{month:02d}-{day_of_month:02d}"

                    # Fire cluster intensity parameters
                    cluster_spread_km = rng.uniform(0.5, 4.5)
                    fire_intensity_factor = rng.lognormal(mean=2.8, sigma=0.8)

                    # 1. MODIS Observations (Terra & Aqua)
                    # MODIS produces 1-4 pixels per typical cluster due to 1km resolution
                    modis_pixels = max(1, int(rng.poisson(1.8)))
                    for _ in range(modis_pixels):
                        sat = "Terra" if rng.rand() < 0.45 else "Aqua"
                        daynight = "D" if rng.rand() < 0.75 else "N"
                        acq_time = f"{rng.choice([10, 11, 13, 14, 21, 22]):02d}{rng.randint(0, 60):02d}"

                        # Offset from center in degrees (~0.01 deg ~= 1.1 km)
                        d_lat = rng.normal(0, cluster_spread_km / 111.0)
                        d_lon = rng.normal(0, cluster_spread_km / (111.0 * np.cos(np.radians(fire_center_lat))))
                        p_lat = round(float(np.clip(fire_center_lat + d_lat, min_lat, max_lat)), 5)
                        p_lon = round(float(np.clip(fire_center_lon + d_lon, min_lon, max_lon)), 5)

                        scan = round(float(rng.uniform(1.0, 2.8)), 2)
                        track = round(float(rng.uniform(1.0, 1.8)), 2)
                        footprint = estimate_pixel_footprint_km2("MODIS", scan, track)
                        _, _, cell_id = get_grid_cell(p_lat, p_lon)

                        # MODIS confidence is percentage [0 - 100]
                        conf_pct = float(np.clip(rng.normal(76, 18), 15, 100))
                        conf_cat = "low" if conf_pct < 30 else ("nominal" if conf_pct < 80 else "high")
                        frp = round(float(rng.lognormal(mean=3.2, sigma=0.7) * (fire_intensity_factor / 15.0)), 1)
                        frp = max(3.5, min(1800.0, frp))
                        brightness = round(float(310.0 + rng.exponential(25.0)), 1)
                        bright_t31 = round(float(brightness - rng.uniform(5.0, 25.0)), 1)

                        records.append({
                            "latitude": p_lat,
                            "longitude": p_lon,
                            "brightness": brightness,
                            "scan": scan,
                            "track": track,
                            "acq_date": acq_date,
                            "acq_time": acq_time,
                            "satellite": sat,
                            "instrument": "MODIS",
                            "confidence": str(int(conf_pct)),
                            "confidence_raw": str(int(conf_pct)),
                            "confidence_cat": conf_cat,
                            "confidence_pct": round(conf_pct, 1),
                            "version": "6.1NRT",
                            "bright_t31": bright_t31,
                            "frp": frp,
                            "daynight": daynight,
                            "footprint_area_km2": footprint,
                            "grid_cell_id": cell_id,
                            "is_duplicate": False,
                            "biome": biome_key
                        })

                    # 2. VIIRS Observations (NOAA-20, NOAA-21, Suomi-NPP)
                    # Due to 375m spatial resolution, VIIRS detects roughly 3.2x to 4.5x more pixels
                    viirs_pixels = max(2, int(modis_pixels * rng.uniform(3.0, 4.4)))
                    for _ in range(viirs_pixels):
                        if year >= 2023:
                            sat = rng.choice(["NOAA-20", "NOAA-21", "Suomi-NPP"], p=[0.45, 0.40, 0.15])
                        else:
                            sat = rng.choice(["NOAA-20", "Suomi-NPP"], p=[0.6, 0.4])

                        daynight = "D" if rng.rand() < 0.7 else "N"
                        acq_time = f"{rng.choice([12, 13, 14, 1, 2]):02d}{rng.randint(0, 60):02d}"

                        d_lat = rng.normal(0, (cluster_spread_km * 0.9) / 111.0)
                        d_lon = rng.normal(0, (cluster_spread_km * 0.9) / (111.0 * np.cos(np.radians(fire_center_lat))))
                        p_lat = round(float(np.clip(fire_center_lat + d_lat, min_lat, max_lat)), 5)
                        p_lon = round(float(np.clip(fire_center_lon + d_lon, min_lon, max_lon)), 5)

                        scan = round(float(rng.uniform(0.32, 0.65)), 2)
                        track = round(float(rng.uniform(0.34, 0.55)), 2)
                        footprint = estimate_pixel_footprint_km2("VIIRS", scan, track)
                        _, _, cell_id = get_grid_cell(p_lat, p_lon)

                        # VIIRS confidence is categorical: 'l', 'n', 'h'
                        conf_cat = rng.choice(["low", "nominal", "high"], p=[0.12, 0.58, 0.30])
                        conf_raw = conf_cat[0]  # 'l', 'n', 'h'
                        conf_pct_map = {"low": 25.0, "nominal": 65.0, "high": 92.0}
                        conf_pct = conf_pct_map[conf_cat]

                        # VIIRS 375m pixel covers smaller area, so pixel-level FRP is typically smaller per pixel
                        frp = round(float(rng.lognormal(mean=2.4, sigma=0.8) * (fire_intensity_factor / 18.0)), 1)
                        frp = max(0.8, min(650.0, frp))
                        brightness = round(float(315.0 + rng.exponential(28.0)), 1)
                        bright_t31 = round(float(brightness - rng.uniform(8.0, 30.0)), 1)

                        records.append({
                            "latitude": p_lat,
                            "longitude": p_lon,
                            "brightness": brightness,
                            "scan": scan,
                            "track": track,
                            "acq_date": acq_date,
                            "acq_time": acq_time,
                            "satellite": sat,
                            "instrument": "VIIRS",
                            "confidence": conf_raw,
                            "confidence_raw": conf_raw,
                            "confidence_cat": conf_cat,
                            "confidence_pct": conf_pct,
                            "version": "2.0NRT",
                            "bright_t31": bright_t31,
                            "frp": frp,
                            "daynight": daynight,
                            "footprint_area_km2": footprint,
                            "grid_cell_id": cell_id,
                            "is_duplicate": False,
                            "biome": biome_key
                        })

    df = pd.DataFrame(records)
    
    # Save output if path specified
    target_path = output_path or (Config.SAMPLE_DIR / "harmonized_sample.csv")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)
    
    # Also save separate MODIS and VIIRS sample files for raw comparisons
    df[df["instrument"] == "MODIS"].to_csv(Config.SAMPLE_DIR / "modis_sample.csv", index=False)
    df[df["instrument"] == "VIIRS"].to_csv(Config.SAMPLE_DIR / "viirs_sample.csv", index=False)

    return df


if __name__ == "__main__":
    df = generate_sample_dataset()
    print(f"Generated {len(df)} sample fire observations across 5 biomes and 2021-2026.")
