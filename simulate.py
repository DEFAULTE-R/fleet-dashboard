import requests, random, time

DEVICES = ["robot-001", "robot-002", "robot-003", "robot-004", "robot-005"]
URL = "http://localhost:8000/api/devices/{}/metrics"

print("🚀 Simulating 5 devices... (Ctrl+C to stop)")
while True:
    for device in DEVICES:
        # robot-003 runs hot to trigger alerts
        temp = random.uniform(85, 95) if device == "robot-003" else random.uniform(45, 72)
        errors = random.randint(12, 20) if device == "robot-004" else random.randint(0, 3)
        data = {
            "cpu_usage": round(random.uniform(20, 90), 1),
            "temperature_c": round(temp, 1),
            "memory_usage": round(random.uniform(30, 85), 1),
            "error_count": errors,
            "tasks_completed": random.randint(100, 5000),
            "uptime_seconds": random.randint(3600, 864000)
        }
        try:
            r = requests.post(URL.format(device), json=data)
            print(f"  ✅ {device} → temp:{data['temperature_c']}°C cpu:{data['cpu_usage']}%")
        except:
            print("  ❌ Server not running? Start it first.")
    time.sleep(3)
