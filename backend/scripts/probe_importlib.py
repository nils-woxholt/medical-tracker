import importlib.util
spec = importlib.util.find_spec('jose')
print('importlib spec for jose:', spec)
