#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger

from tux.database.service import DatabaseService


async def analyze_performance():
    """Analyze database performance metrics."""
    logger.info("📊 Analyzing database performance metrics...")

    try:
        service = DatabaseService(echo=False)
        await service.connect()

        metrics = await service.get_database_metrics()

        # Pool metrics
        logger.info("🔄 Connection Pool Status:")
        for key, value in metrics.get("pool", {}).items():
            logger.info(f"  {key.replace('_', ' ').title()}: {value}")

        # Table statistics
        logger.info("📋 Table Statistics:")
        controllers = [
            ("guild", service.guild),
            ("guild_config", service.guild_config),
            ("case", service.case),
        ]

        for name, controller in controllers:
            try:
                stats = await controller.get_table_statistics()
                if stats:
                    logger.info(f"  {name.title()}:")
                    for key, value in stats.items():
                        if value is not None:
                            logger.info(f"    {key.replace('_', ' ').title()}: {value}")
            except Exception as e:
                logger.warning(f"  Could not get stats for {name}: {e}")

    except Exception as e:
        logger.error(f"❌ Performance analysis failed: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    exit_code = asyncio.run(analyze_performance())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
