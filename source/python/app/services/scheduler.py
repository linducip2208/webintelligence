"""Cron/interval next-run — stdlib only."""
import datetime
def next_run(kind: str, every_min=60, hour=2, weekday=None):
    now = datetime.datetime.utcnow()
    if kind == "interval": return now + datetime.timedelta(minutes=every_min)
    if kind == "hourly": return (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    if kind == "daily": return (now + datetime.timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
    if kind == "weekly": return (now + datetime.timedelta(days=7)).replace(hour=hour, minute=0, second=0, microsecond=0)
    return now
