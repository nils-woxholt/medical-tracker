from app.telemetry.metrics_auth import inc_login
from app.telemetry.metrics import metrics_registry

inc_login("success")
inc_login("failure")
for line in metrics_registry.collect_metrics().decode().splitlines():
    if line.startswith("authentication_attempts_total"):
        print(line)
