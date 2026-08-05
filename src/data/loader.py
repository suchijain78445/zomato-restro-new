import json
import logging
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from src.config import settings
from src.data.preprocessor import preprocess_dataframe

logger = logging.getLogger(__name__)


def load_raw_huggingface_dataset(
    dataset_name: str = settings.DATASET_NAME,
) -> pd.DataFrame:
    """
    Loads raw Zomato dataset from Hugging Face datasets library.
    """
    logger.info(f"Downloading/loading dataset '{dataset_name}' from Hugging Face...")
    ds = load_dataset(dataset_name, split="train")
    return ds.to_pandas()


def generate_and_save_metadata(
    df: pd.DataFrame, metadata_dir_path: str = settings.METADATA_DIR
) -> dict:
    """
    Generates metadata JSON files from processed DataFrame:
    - cities.json
    - locations.json
    - cuisines.json
    """
    meta_dir = Path(metadata_dir_path)
    meta_dir.mkdir(parents=True, exist_ok=True)

    # 1. Cities
    cities = sorted(
        [
            str(c).strip()
            for c in df["city"].unique()
            if pd.notna(c) and str(c).strip() and str(c).strip() != "nan"
        ]
    )

    # 2. Locations per city
    locations_by_city = {}
    for city_name, group in df.groupby("city"):
        if not pd.notna(city_name) or str(city_name).strip() == "nan":
            continue
        clean_city = str(city_name).strip()
        locs = sorted(
            list(
                {
                    str(loc).strip()
                    for loc in group["location"].unique()
                    if pd.notna(loc) and str(loc).strip() and str(loc).strip() != "nan"
                }
            )
        )
        locations_by_city[clean_city] = locs


    # 3. All unique cuisines
    all_cuisines = set()
    for cuisines_list in df["cuisines"]:
        if isinstance(cuisines_list, (list, tuple)):
            for c in cuisines_list:
                if c:
                    all_cuisines.add(c)
    cuisines = sorted(list(all_cuisines))

    # Save to JSON
    cities_file = meta_dir / "cities.json"
    locations_file = meta_dir / "locations.json"
    cuisines_file = meta_dir / "cuisines.json"

    with open(cities_file, "w", encoding="utf-8") as f:
        json.dump(cities, f, indent=2, ensure_ascii=False)

    with open(locations_file, "w", encoding="utf-8") as f:
        json.dump(locations_by_city, f, indent=2, ensure_ascii=False)

    with open(cuisines_file, "w", encoding="utf-8") as f:
        json.dump(cuisines, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Metadata files generated: {len(cities)} cities, "
        f"{sum(len(v) for v in locations_by_city.values())} locations, "
        f"{len(cuisines)} cuisines saved to {meta_dir}."
    )

    return {
        "cities": cities,
        "locations": locations_by_city,
        "cuisines": cuisines,
    }


def save_processed_data(
    df: pd.DataFrame, parquet_path_str: str = settings.DATA_CACHE_PATH
) -> None:
    """
    Saves processed DataFrame to Parquet format.
    """
    parquet_path = Path(parquet_path_str)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, engine="pyarrow", index=False)
    logger.info(f"Processed dataset ({len(df)} rows) saved to '{parquet_path}'.")


def load_processed_data(
    parquet_path_str: str = settings.DATA_CACHE_PATH,
) -> pd.DataFrame:
    """
    Reads processed DataFrame from Parquet cache.
    """
    parquet_path = Path(parquet_path_str)
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet dataset cache not found at '{parquet_path}'.")
    return pd.read_parquet(parquet_path, engine="pyarrow")


def get_or_create_processed_data(
    force_reprocess: bool = False,
    parquet_path_str: str = settings.DATA_CACHE_PATH,
    metadata_dir_str: str = settings.METADATA_DIR,
) -> pd.DataFrame:
    """
    Loads dataset from Parquet cache if present; otherwise downloads from HuggingFace,
    preprocesses, saves Parquet cache, and exports metadata JSONs.
    """
    parquet_path = Path(parquet_path_str)
    if parquet_path.exists() and not force_reprocess:
        logger.info(f"Loading cached dataset from {parquet_path}...")
        return load_processed_data(parquet_path_str)

    logger.info("Cached dataset not found or reprocess requested. Starting ETL...")
    raw_df = load_raw_huggingface_dataset()
    processed_df = preprocess_dataframe(raw_df)
    save_processed_data(processed_df, parquet_path_str)
    generate_and_save_metadata(processed_df, metadata_dir_str)
    return processed_df
