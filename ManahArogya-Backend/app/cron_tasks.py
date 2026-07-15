from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings


logger = logging.getLogger("cron.api")


def run_heartbeat() -> int:
    now = datetime.now(timezone.utc).isoformat()
    logger.info("API cron heartbeat at %s for service %s", now, settings.app_name)
    print(f"API heartbeat OK | service={settings.app_name} | timestamp_utc={now}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m app.cron_tasks heartbeat", file=sys.stderr)
        return 2

    command = sys.argv[1].strip().lower()
    if command == "heartbeat":
        return run_heartbeat()

    print(f"Unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
