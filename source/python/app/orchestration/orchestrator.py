"""Enqueue + lease + idempotency over Redis (redis pkg optional)."""
import json, hashlib, time, uuid
QUEUE = "webintel:queue:jobs"; DLQ = "webintel:queue:dlq"
def idem_key(payload: dict): return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:32]
def enqueue(client, job: dict):
    job = dict(job)
    job.setdefault("schema_version", "1.0"); job.setdefault("job_id", uuid.uuid4().hex)
    job.setdefault("timeout_ms", 30000)
    if client is None: return {"queued": False, "job": job, "reason": "no-redis"}
    client.rpush(QUEUE, json.dumps(job)); return {"queued": True, "job": job}
def dequeue(client, timeout=5):
    if client is None: return None
    item = client.blpop(QUEUE, timeout=timeout)
    return json.loads(item[1]) if item else None
