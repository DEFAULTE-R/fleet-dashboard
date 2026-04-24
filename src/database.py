import sqlite3
from pathlib import Path

DB_PATH = Path("fleet.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            created_at TEXT DEFAULT (datetime('now')),
            last_seen TEXT DEFAULT (datetime('now'))
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp TEXT,
            cpu_usage REAL,
            temperature_c REAL,
            memory_usage REAL,
            error_count INTEGER,
            tasks_completed INTEGER,
            uptime_seconds INTEGER
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            alert_type TEXT,
            message TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            resolved INTEGER DEFAULT 0
        )
        """)

def upsert_device(device_id: str):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO devices (device_id, last_seen)
        VALUES (?, datetime('now'))
        ON CONFLICT(device_id)
        DO UPDATE SET last_seen=datetime('now')
        """, (device_id,))

def insert_metrics(device_id: str, data: dict):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO metrics (
            device_id, timestamp, cpu_usage, temperature_c,
            memory_usage, error_count, tasks_completed, uptime_seconds
        ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?)
        """, (
            device_id,
            data["cpu_usage"],
            data["temperature_c"],
            data["memory_usage"],
            data["error_count"],
            data["tasks_completed"],
            data["uptime_seconds"]
        ))

        if data["temperature_c"] > 90:
            conn.execute("""
            INSERT INTO alerts (device_id, alert_type, message)
            VALUES (?, 'OVERHEAT', 'Temperature > 90C')
            """, (device_id,))

        if data["error_count"] > 15:
            conn.execute("""
            INSERT INTO alerts (device_id, alert_type, message)
            VALUES (?, 'ERROR_SPIKE', 'High error count')
            """, (device_id,))

def compute_health(temp, cpu, errors):
    score = 100

    score -= max(0, temp - 50) * 0.8
    score -= max(0, cpu - 60) * 0.5
    score -= errors * 2

    return max(0, min(100, round(score, 1)))

def get_all_devices():
    with get_conn() as conn:
        rows = conn.execute("""
        SELECT d.device_id, m.*
        FROM devices d
        LEFT JOIN metrics m ON d.device_id = m.device_id
        WHERE m.id = (
            SELECT id FROM metrics
            WHERE device_id = d.device_id
            ORDER BY timestamp DESC LIMIT 1
        )
        """).fetchall()

        result = []
        for r in rows:
            if not r["temperature_c"]:
                continue

            health = compute_health(
                r["temperature_c"],
                r["cpu_usage"],
                r["error_count"]
            )

            if health < 40:
                status = "error"
            elif health < 70:
                status = "warning"
            else:
                status = "healthy"

            result.append({
                "device_id": r["device_id"],
                "temperature_c": r["temperature_c"],
                "cpu_usage": r["cpu_usage"],
                "memory_usage": r["memory_usage"],
                "error_count": r["error_count"],
                "health": health,
                "status": status
            })

        return result

def get_device_metrics(device_id: str):
    with get_conn() as conn:
        rows = conn.execute("""
        SELECT * FROM metrics
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT 50
        """, (device_id,)).fetchall()

        return [dict(r) for r in rows]

def get_alerts():
    with get_conn() as conn:
        rows = conn.execute("""
        SELECT * FROM alerts
        ORDER BY created_at DESC
        LIMIT 50
        """).fetchall()

        return [dict(r) for r in rows]
