from flask import Flask, request, jsonify
import requests
from datetime import datetime
import json
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

# ==========================================
# TELEGRAM SETTINGS
# ==========================================


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ==========================================
# LOAD LAST LEAD ID
# ==========================================

with open("counter.json", "r") as file:
    counter_data = json.load(file)

lead_counter = counter_data["last_lead_id"]


# ==========================================
# FUNCTION 1: DECIDE WHETHER LEAD QUALIFIES
# ==========================================

def qualify_lead(lead):

    # VIP leads automatically qualify
    if lead["vip_status"]:
        return True

    # Normal qualification rules
    if (
        lead["interested"]
        and lead["appointment_booked"]
        and lead["budget"] >= 50000
        and lead["age"] >= 18
    ):
        return True

    return False


# ==========================================
# FUNCTION 2: VALIDATE LEAD
# ==========================================

def validate_lead(lead):

    # Check if we received JSON
    if not lead:
        return "No lead data received"

    # Required fields
    required_fields = [
        "name",
        "email",
        "budget",
        "interested",
        "vip_status",
        "age",
        "appointment_booked"
    ]

    # Check for missing fields
    missing_fields = []

    for field in required_fields:

        if field not in lead:
            missing_fields.append(field)

    if missing_fields:
        return f"Missing required fields: {missing_fields}"

    # Check budget
    if not isinstance(lead["budget"], (int, float)):
        return "Budget must be a number"

    # Check negative budget
    if lead["budget"] < 0:
        return "Budget cannot be negative"

    # Check age
    if not isinstance(lead["age"], int):
        return "Age must be a whole number"

    # Check age range
    if lead["age"] < 18 or lead["age"] > 100:
        return "Age must be between 18 and 100"

    # Check email
    if "@" not in lead["email"] or "." not in lead["email"]:
        return "Invalid email address"

    # Check name
    if not isinstance(lead["name"], str) or not lead["name"].strip():
        return "Name must be provided"

    # Check boolean fields
    boolean_fields = [
        "interested",
        "vip_status",
        "appointment_booked"
    ]

    for field in boolean_fields:

        if not isinstance(lead[field], bool):
            return f"{field} must be true or false"

    # Everything passed
    return None


# ==========================================
# FUNCTION 3: SEND LEAD TO CRM
# ==========================================

def send_to_crm(lead):

    # Prepare lead for CRM
    crm_lead = {
        "lead_id": lead["lead_id"],
        "name": lead["name"],
        "email": lead["email"],
        "budget": lead["budget"],
        "status": lead["status"]
    }

    # CRM URL
    url = "https://jsonplaceholder.typicode.com/posts"

    try:

        response = requests.post(
            url,
            json=crm_lead,
            timeout=5
        )

        if response.status_code == 201:

            print("CRM: Lead sent successfully")
            return "sent"

        else:

            print("CRM ERROR:", response.status_code)
            return "failed"

    except requests.exceptions.RequestException as error:

        print("CONNECTION ERROR:", error)
        return "failed"


# ==========================================
# FUNCTION 4: SEND TELEGRAM NOTIFICATION
# ==========================================

def send_notification(lead):

    message = (
        "🚨 NEW QUALIFIED LEAD 🚨\n\n"
        f"👤 Name: {lead['name']}\n"
        f"📧 Email: {lead['email']}\n"
        f"💰 Budget: ₱{lead['budget']:,}\n"
        f"🆔 Lead ID: {lead['lead_id']}\n"
        f"📅 Appointment: "
        f"{'Booked' if lead['appointment_booked'] else 'Not booked'}\n"
        f"⭐ VIP: {'Yes' if lead['vip_status'] else 'No'}\n"
        f"🕐 Received: {lead['received_at']}\n"
        f"🎯 Status: {lead['status']}"
    )

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    try:

        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=5
        )

        if response.status_code == 200:

            print("Telegram: Notification sent successfully")
            return "sent"

        else:

            print("Telegram ERROR:", response.status_code)
            print(response.text)
            return "failed"

    except requests.exceptions.RequestException as error:

        print("Telegram CONNECTION ERROR:", error)
        return "failed"


# ==========================================
# WEBHOOK
# ==========================================

@app.route("/webhook", methods=["POST"])
def receive_lead():

    global lead_counter

    # ==========================================
    # RECEIVE LEAD
    # ==========================================

    lead = request.json

    # ==========================================
    # VALIDATE LEAD
    # ==========================================

    validation_error = validate_lead(lead)

    if validation_error:

        return jsonify({
            "error": validation_error
        }), 400

    # ==========================================
    # PRINT NEW LEAD
    # ==========================================

    print("NEW LEAD RECEIVED:")
    print(lead)

    # ==========================================
    # CREATE LEAD ID
    # ==========================================

    lead_counter += 1

    # Save new Lead ID
    with open("counter.json", "w") as file:

        json.dump({
            "last_lead_id": lead_counter
        }, file)

    # Add Lead ID to lead
    lead["lead_id"] = f"LEAD-{lead_counter:03d}"

    # ==========================================
    # ADD TIMESTAMP
    # ==========================================

    lead["received_at"] = datetime.now().isoformat()

    # ==========================================
    # QUALIFY LEAD
    # ==========================================

    if qualify_lead(lead):

        # Lead is qualified
        lead["status"] = "qualified"

        print("QUALIFIED LEAD")

        # ==========================================
        # SEND TO CRM
        # ==========================================

        crm_status = send_to_crm(lead)

        # ==========================================
        # SEND TELEGRAM NOTIFICATION
        # ==========================================

        if crm_status == "sent":

            notification_status = send_notification(lead)

        else:

            notification_status = "not sent"

    else:

        # Lead is not qualified
        lead["status"] = "not qualified"

        print("NOT QUALIFIED")

        crm_status = "not sent"
        notification_status = "not sent"

    # ==========================================
    # RETURN RESPONSE
    # ==========================================

    return jsonify({

        "lead": lead,

        "crm_status": crm_status,

        "notification_status": notification_status

    }), 200


# ==========================================
# START FLASK
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)