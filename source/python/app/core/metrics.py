REG = {}
def inc(name, v=1): REG[name] = REG.get(name, 0) + v
def setv(name, v): REG[name] = v
def render():
    return "\n".join(f"# TYPE {k} gauge\n{k} {v}" for k, v in sorted(REG.items())) + "\n"
