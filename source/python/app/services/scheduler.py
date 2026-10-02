"""Cron/interval next-run — stdlib only."""
import datetime


def _match(field: str, value: int) -> bool:
    field = field.strip()
    if field == "*":
        return True
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            step = int(step)
            lo = 0 if base == "*" else int(base.split("-")[0])
            if value >= lo and (value - lo) % step == 0:
                return True
        elif "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
            if lo <= value <= hi:
                return True
        elif part == str(value):
            return True
    return False


def cron_next(expr: str, now: datetime.datetime = None) -> datetime.datetime:
    """Next UTC minute matching a 5-field cron (min hour dom month dow)."""
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError("cron needs 5 fields")
    now = now or datetime.datetime.utcnow()
    cand = (now + datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)
    for _ in range(525600):  # up to 1 year
        if (_match(parts[0], cand.minute) and _match(parts[1], cand.hour)
                and _match(parts[2], cand.day) and _match(parts[3], cand.month)
                and _match(parts[4], (cand.weekday() + 1) % 7)):
            return cand
        cand += datetime.timedelta(minutes=1)
    raise ValueError("no cron match within a year")


def next_run(kind: str, every_min=60, hour=2, weekday=None, cron=""):
    now = datetime.datetime.utcnow()
    if kind == "interval": return now + datetime.timedelta(minutes=every_min)
    if kind == "hourly": return (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    if kind == "daily": return (now + datetime.timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
    if kind == "weekly": return (now + datetime.timedelta(days=7)).replace(hour=hour, minute=0, second=0, microsecond=0)
    if kind == "cron": return cron_next(cron or "*/30 * * * *", now)
    return now
