from flask import Flask, request, jsonify
import requests
from datetime import datetime
import json
import sqlite3
from dotenv import load_dotenv
import os
from functools import wraps
from qualification import qualify_lead
from validation import validate_lead
from crm import send_to_crm
from notifications import send_notification
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