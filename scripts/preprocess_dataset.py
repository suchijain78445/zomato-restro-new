#!/usr/bin/env python3
"""
CLI script to trigger downloading, preprocessing, Parquet caching,
and metadata JSON generation for the Zomato restaurant dataset.
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.data.loader import get_or_create_processed_data  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("preprocess_dataset")


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess Zomato restaurant dataset"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download and reprocessing even if Parquet cache exists",
    )
    args = parser.parse_args()

    logger.info("Starting dataset preprocessing pipeline...")
    df = get_or_create_processed_data(force_reprocess=args.force)
    logger.info(
        f"Pipeline completed successfully. Total restaurants in dataset: {len(df)}"
    )


if __name__ == "__main__":
    main()
