from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone


logger = logging.getLogger("cron.worker")

REQUIRED_ENV_VARS = ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")


def run_heartbeat() -> int:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        logger.error("LiveKit worker cron heartbeat failed. Missing env vars: %s", ", ".join(missing))
        print(f"Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc).isoformat()
    logger.info("Worker cron heartbeat at %s. LiveKit env looks configured.", now)
    print(f"Worker heartbeat OK | timestamp_utc={now}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m app.agents.cron_tasks heartbeat", file=sys.stderr)
        return 2

    command = sys.argv[1].strip().lower()
    if command == "heartbeat":
        return run_heartbeat()

    print(f"Unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
