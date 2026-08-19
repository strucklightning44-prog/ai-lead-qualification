import sqlite3


# Connect to the database
connection = sqlite3.connect("leads.db")

# Create a cursor
cursor = connection.cursor()


# Get all leads
cursor.execute("""
    SELECT
        lead_id,
        name,
        email,
        budget,
        status
    FROM leads
    ORDER BY id
""")


# Get the results
leads = cursor.fetchall()


# Display the leads
print("\n========== ALL LEADS ==========\n")

if not leads:

    print("No leads found.")

else:

    for lead in leads:

        lead_id, name, email, budget, status = lead

        print(f"Lead ID: {lead_id}")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Budget: ₱{budget:,.2f}")
        print(f"Status: {status}")
        print("--------------------------------")


# Close the database connection
connection.close()