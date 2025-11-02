# Royalty Compliance & Financial Audit (2legit4it)
OWNER = "Dwayne Anthony Brian Galloway"
PROJECTNAME = "2legit4it"
ROYALTY_RATE = 0.10

def enforce_royalty(revenue):
    royalty_due = revenue * ROYALTY_RATE
    print(f"Royalty for {PROJECTNAME}: £{royalty_due:.2f} owed to {OWNER}")
    return royalty_due

def log_audit(event, user, details):
    import sqlite3, datetime
    conn = sqlite3.connect("2legit4it.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY,
            event TEXT,
            user TEXT,
            timestamp TEXT,
            details TEXT
        )
    """)
    ts = datetime.datetime.utcnow().isoformat("T") + "Z"
    cur.execute("INSERT INTO audit_log(event, user, timestamp, details) VALUES (?, ?, ?, ?)",
                (event, user, ts, details))
    conn.commit()
    conn.close()