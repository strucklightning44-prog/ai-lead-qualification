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
            received_at TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("Database created successfully!")


def save_lead(lead):

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

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
            received_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        lead["received_at"]
    ))

    connection.commit()
    connection.close()

    print("Lead saved to database!")


if __name__ == "__main__":
    create_database()