"""Enterprise Demo Reset Script — Go Chicken Hackathon Pivot.

1-command utility to wipe existing database state and restore pristine "Day 1" demo state.
Useful before presentations, judging sessions, or after testing live WhatsApp/API flows.

Usage:
    python -m scripts.reset_demo
    OR
    python scripts/reset_demo.py
"""

import asyncio
import logging
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.seed_demo import main as seed_main

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("go_chicken.reset_demo")


async def reset_demo():
    logger.info("==================================================================")
    logger.info("🔄 GO CHICKEN ENTERPRISE DEMO RESET — RESTORING DAY 1 STATE")
    logger.info("==================================================================")
    
    # Invokes schema verification, reverse-FK truncation, and full relational seeding
    await seed_main()
    
    logger.info("==================================================================")
    logger.info("✨ DEMO RESET COMPLETE! All dashboards & APIs are reset to pristine state.")
    logger.info("==================================================================")


if __name__ == "__main__":
    asyncio.run(reset_demo())
