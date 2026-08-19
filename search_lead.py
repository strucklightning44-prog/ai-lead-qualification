import sqlite3


# Ask the user for an email
email = input("Enter lead email: ")


# Connect to database
connection = sqlite3.connect("leads.db")

cursor = connection.cursor()


# Search for the lead
cursor.execute("""
    SELECT
        lead_id,
        name,
        email,
        budget,
        status
    FROM leads
    WHERE email = ?
""", (email,))


# Get the result
lead = cursor.fetchone()


# Check if we found the lead
if lead:

    lead_id, name, email, budget, status = lead

    print("\n========== LEAD FOUND ==========")
    print(f"Lead ID: {lead_id}")
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Budget: ₱{budget:,.2f}")
    print(f"Status: {status}")

else:

    print("\nLead not found.")


# Close database
connection.close()