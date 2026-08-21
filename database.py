import sqlite3


def create_database():

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT UNIQUE,
            name TEXT,
            email TEXT,
            budget REAL,
            interested BOOLEAN,
            vip_status BOOLEAN,
            age INTEGER,
            appointment_booked BOOLEAN,
            status TEXT,
            received_at TEXT,
            lead_score INTEGER,
            lead_priority TEXT,
            follow_up_action TEXT,
            follow_up_timeframe TEXT,
            follow_up_due_at TEXT,
            follow_up_status TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("Database created successfully!")


def save_lead(lead):

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    follow_up = lead.get("follow_up", {})

    cursor.execute("""
        INSERT INTO leads (
            lead_id,
            name,
            email,
            budget,
            interested,
            vip_status,
            age,
            appointment_booked,
            status,
            received_at,
            lead_score,
            lead_priority,
            follow_up_action,
            follow_up_timeframe,
            follow_up_due_at,
            follow_up_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead["lead_id"],
        lead["name"],
        lead["email"],
        lead["budget"],
        lead["interested"],
        lead["vip_status"],
        lead["age"],
        lead["appointment_booked"],
        lead["status"],
        lead["received_at"],
        lead.get("lead_score"),
        lead.get("lead_priority"),
        follow_up.get("action"),
        follow_up.get("timeframe"),
        follow_up.get("due_at"),
        follow_up.get("status", "pending")
    ))

    connection.commit()
    connection.close()

    print("Lead saved to database!")