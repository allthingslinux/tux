#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger

from tux.database.service import DatabaseService


async def health_check():
    """Perform comprehensive database health check."""
    logger.info("🏥 Running comprehensive database health check...")

    try:
        service = DatabaseService(echo=False)
        await service.connect()

        health = await service.health_check()

        if health["status"] == "healthy":
            logger.success("✅ Database is healthy!")

            # Log health metrics
            for key, value in health.items():
                if key != "status":
                    logger.info(f"  {key.replace('_', ' ').title()}: {value}")
        else:
            logger.error(f"❌ Database unhealthy: {health.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    exit_code = asyncio.run(health_check())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
