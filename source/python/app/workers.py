"""Background worker: schedules, ETL, alerts (run via systemd webintel-worker)."""
import time

from .core.logging import log
from .services.scheduler import next_run


def main():
    log("worker-boot")
    while True:
        nxt = next_run("interval", every_min=5)
        log("worker-tick", next_run=str(nxt))
        time.sleep(60)


if __name__ == "__main__":
    main()
