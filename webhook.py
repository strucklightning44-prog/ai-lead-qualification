from flask import Flask, request, jsonify
import requests
from datetime import datetime
import json
import sqlite3
from dotenv import load_dotenv
import os
from functools import wraps
from database import save_lead
app = Flask(__name__)
load_dotenv()
# ==========================================
# API KEY AUTHENTICATION DECORATOR
# ==========================================

def require_api_key(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        api_key = request.headers.get("X-API-Key")

        if api_key != API_KEY:

            return jsonify({
                "error": "Unauthorized"
            }), 401

        return function(*args, **kwargs)

    return decorated_function
API_KEY = os.getenv("API_KEY")
# ==========================================
# API KEY AUTHENTICATION
# ==========================================

def authenticate_request():

    api_key = request.headers.get("X-API-Key")

    if api_key != API_KEY:
        return False

    return True
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
# GET ALL LEADS
# ==========================================

@app.route("/leads", methods=["GET"])
@require_api_key
def get_all_leads():
    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

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

    leads = cursor.fetchall()

    connection.close()

    results = []

    for lead in leads:

        results.append({
            "lead_id": lead[0],
            "name": lead[1],
            "email": lead[2],
            "budget": lead[3],
            "status": lead[4]
        })

    return jsonify({
        "count": len(results),
        "leads": results
    }), 200
# ==========================================
# WEBHOOK
# ==========================================

@app.route("/webhook", methods=["POST"])
@require_api_key
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
        save_lead(lead)

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
        save_lead(lead)
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
# SEARCH LEAD BY EMAIL
# ==========================================

@app.route("/leads/<email>", methods=["GET"])
@require_api_key
def get_lead(email):

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
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
        FROM leads
        WHERE email = ?
    """, (email,))

    lead = cursor.fetchone()

    connection.close()

    if not lead:
        return jsonify({
            "error": "Lead not found"
        }), 404

    return jsonify({
        "lead_id": lead[0],
        "name": lead[1],
        "email": lead[2],
        "budget": lead[3],
        "interested": bool(lead[4]),
        "vip_status": bool(lead[5]),
        "age": lead[6],
        "appointment_booked": bool(lead[7]),
        "status": lead[8],
        "received_at": lead[9]
    }), 200
# ==========================================
# UPDATE LEAD STATUS
# ==========================================

@app.route("/leads/<email>", methods=["PUT"])
@require_api_key
def update_lead(email):

    data = request.json

    if not data:
        return jsonify({
            "error": "No data received"
        }), 400

    if "status" not in data:
        return jsonify({
            "error": "Status is required"
        }), 400

    allowed_statuses = [
        "qualified",
        "contacted",
        "appointment",
        "closed",
        "not qualified"
    ]

    if data["status"] not in allowed_statuses:
        return jsonify({
            "error": "Invalid status",
            "allowed_statuses": allowed_statuses
        }), 400

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE leads
        SET status = ?
        WHERE email = ?
    """, (data["status"], email))

    if cursor.rowcount == 0:

        connection.close()

        return jsonify({
            "error": "Lead not found"
        }), 404

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Lead status updated successfully",
        "email": email,
        "status": data["status"]
    }), 200
# ==========================================
# SEARCH LEADS
# ==========================================

@app.route("/leads/search", methods=["GET"])
@require_api_key
def search_leads():

    status = request.args.get("status")
    min_budget = request.args.get("min_budget")

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    # Start with the basic query
    query = """
        SELECT
            lead_id,
            name,
            email,
            budget,
            status
        FROM leads
        WHERE 1=1
    """

    parameters = []

    # Filter by status
    if status:

        query += " AND status = ?"

        parameters.append(status)

    # Filter by minimum budget
    if min_budget:

        try:
            min_budget = float(min_budget)

        except ValueError:

            connection.close()

            return jsonify({
                "error": "min_budget must be a number"
            }), 400

        query += " AND budget >= ?"

        parameters.append(min_budget)

    query += " ORDER BY id"

    cursor.execute(query, parameters)

    leads = cursor.fetchall()

    connection.close()

    results = []

    for lead in leads:

        results.append({
            "lead_id": lead[0],
            "name": lead[1],
            "email": lead[2],
            "budget": lead[3],
            "status": lead[4]
        })

    return jsonify({
        "count": len(results),
        "leads": results
    }), 200
# ==========================================
# DELETE LEAD
# ==========================================

@app.route("/leads/<email>", methods=["DELETE"])
@require_api_key
def delete_lead(email):

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM leads
        WHERE email = ?
    """, (email,))

    if cursor.rowcount == 0:

        connection.close()

        return jsonify({
            "error": "Lead not found"
        }), 404

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Lead deleted successfully",
        "email": email
    }), 200    
# ==========================================
# START FLASK
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)