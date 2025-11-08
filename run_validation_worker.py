#!/usr/bin/env python3
"""
Validation Worker Entry Point

Starts the validation worker to process messages from Redis queues.
This worker validates incoming data before it's enriched and stored in the database.

Usage:
    python run_validation_worker.py
"""

import sys
import logging
from src.pipeline.validation.validation_worker import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        main()
    except KeyboardInterrupt:
        logging.info("Validation worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
