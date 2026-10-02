import datetime
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from services.scheduler import cron_next, next_run


def test_cron_every_5():
    now = datetime.datetime(2026, 10, 2, 10, 3, 0)
    nxt = cron_next("*/5 * * * *", now)
    assert (nxt - now).total_seconds() == 120
    assert nxt.minute % 5 == 0


def test_cron_daily_2am():
    now = datetime.datetime(2026, 10, 2, 10, 0, 0)
    nxt = cron_next("0 2 * * *", now)
    assert (nxt.hour, nxt.minute) == (2, 0) and nxt.day == 3


def test_cron_lists_ranges_steps():
    now = datetime.datetime(2026, 10, 5, 0, 0, 0)  # Monday
    nxt = cron_next("0 9 * * 1", now)  # Monday 09:00
    assert nxt.weekday() == 0 and (nxt.hour, nxt.minute) == (9, 0)
    nxt2 = cron_next("0 0 1 * *", now)
    assert nxt2.day == 1


def test_cron_bad():
    try:
        cron_next("not a cron")
        assert False
    except ValueError:
        pass


def test_next_run_kinds():
    assert next_run("interval", every_min=5) > datetime.datetime.utcnow()
    assert next_run("cron", cron="*/15 * * * *") > datetime.datetime.utcnow()
