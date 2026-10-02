def check(name, ok, detail=""):
    return {"name": name, "status": "up" if ok else "down", "detail": detail}
def overall(checks):
    return "healthy" if all(c["status"] == "up" for c in checks) and checks else "degraded"
