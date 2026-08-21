import sqlite3


connection = sqlite3.connect("leads.db")

cursor = connection.cursor()


columns = [
    ("lead_score", "INTEGER"),
    ("lead_priority", "TEXT"),
    ("follow_up_action", "TEXT"),
    ("follow_up_timeframe", "TEXT"),
    ("follow_up_due_at", "TEXT"),
    ("follow_up_status", "TEXT")
]


for column_name, column_type in columns:

    try:

        cursor.execute(
            f"ALTER TABLE leads ADD COLUMN {column_name} {column_type}"
        )

        print(f"Added column: {column_name}")

    except sqlite3.OperationalError:

        print(f"Column already exists: {column_name}")


connection.commit()

connection.close()

print("Database migration completed!")