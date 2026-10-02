_REG = {}
def register(name, provider): _REG[name] = provider
def get(name): return _REG.get(name)
def names(): return sorted(_REG)
