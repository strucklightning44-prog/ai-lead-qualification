from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime
import os
import sqlite3
from functools import wraps

from qualification import qualify_lead
from validation import validate_lead
from crm import send_to_crm
from notifications import send_notification
from lead_id import generate_lead_id
from database import create_database, save_lead
from lead_scoring import calculate_lead_score, get_lead_priority
from follow_up import create_follow_up


app = Flask(__name__)

load_dotenv()

create_database()


# ==========================================
# API KEY
# ==========================================

API_KEY = os.getenv("API_KEY")


# ==========================================
# TELEGRAM SETTINGS
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


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
            status,
            lead_score,
            lead_priority
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
            "status": lead[4],
            "lead_score": lead[5],
            "lead_priority": lead[6]
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

    lead["lead_id"] = generate_lead_id()

    # ==========================================
    # ADD TIMESTAMP
    # ==========================================

    lead["received_at"] = datetime.now().isoformat()

    # ==========================================
    # CALCULATE LEAD SCORE
    # ==========================================

    lead["lead_score"] = calculate_lead_score(lead)

    lead["lead_priority"] = get_lead_priority(
        lead["lead_score"]
    )

    print("LEAD SCORE:", lead["lead_score"])
    print("LEAD PRIORITY:", lead["lead_priority"])

    # ==========================================
    # QUALIFY LEAD
    # ==========================================

    qualified, reasons = qualify_lead(lead)

    # ==========================================
    # QUALIFIED LEAD
    # ==========================================

    if qualified:

        lead["status"] = "qualified"

        # ==========================================
        # CREATE FOLLOW-UP
        # ==========================================

        lead["follow_up"] = create_follow_up(lead)

        print("QUALIFIED LEAD")
        print("FOLLOW-UP:", lead["follow_up"])

        # ==========================================
        # SAVE LEAD
        # ==========================================

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

            lead["notification_type"] = "crm_failed"

            notification_status = send_notification(lead)

    # ==========================================
    # NOT QUALIFIED LEAD
    # ==========================================

    else:

        lead["status"] = "not qualified"

        lead["qualification_reasons"] = reasons

        print("NOT QUALIFIED")
        print("Reasons:", reasons)

        # ==========================================
        # SAVE LEAD
        # ==========================================

        save_lead(lead)

        crm_status = "not sent"

        # ==========================================
        # SEND TELEGRAM NOTIFICATION
        # ==========================================

        notification_status = send_notification(lead)

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
            received_at,
            lead_score,
            lead_priority
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
        "received_at": lead[9],
        "lead_score": lead[10],
        "lead_priority": lead[11]

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
    """, (
        data["status"],
        email
    ))

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
# UPDATE FOLLOW-UP STATUS
# ==========================================

@app.route("/leads/<email>/follow-up", methods=["PUT"])
@require_api_key
def update_follow_up(email):

    data = request.json

    if not data:

        return jsonify({
            "error": "No data received"
        }), 400

    if "follow_up_status" not in data:

        return jsonify({
            "error": "follow_up_status is required"
        }), 400

    allowed_statuses = [
        "pending",
        "contacted",
        "appointment",
        "completed"
    ]

    follow_up_status = data["follow_up_status"].lower()

    if follow_up_status not in allowed_statuses:

        return jsonify({
            "error": "Invalid follow-up status",
            "allowed_statuses": allowed_statuses
        }), 400

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE leads
        SET follow_up_status = ?
        WHERE email = ?
    """, (
        follow_up_status,
        email
    ))

    if cursor.rowcount == 0:

        connection.close()

        return jsonify({
            "error": "Lead not found"
        }), 404

    connection.commit()

    connection.close()

    return jsonify({

        "message": "Follow-up status updated successfully",

        "email": email,

        "follow_up_status": follow_up_status

    }), 200
# ==========================================
# GET FOLLOW-UPS
# ==========================================

@app.route("/follow-ups", methods=["GET"])
@require_api_key
def get_follow_ups():

    status = request.args.get("status")

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    query = """
        SELECT
            lead_id,
            name,
            email,
            lead_priority,
            follow_up_action,
            follow_up_timeframe,
            follow_up_status
        FROM leads
        WHERE follow_up_action IS NOT NULL
    """

    parameters = []

    # ==========================================
    # FILTER BY FOLLOW-UP STATUS
    # ==========================================

    if status:

        allowed_statuses = [
            "pending",
            "contacted",
            "appointment",
            "completed"
        ]

        status = status.lower()

        if status not in allowed_statuses:

            connection.close()

            return jsonify({
                "error": "Invalid follow-up status",
                "allowed_statuses": allowed_statuses
            }), 400

        query += " AND follow_up_status = ?"

        parameters.append(status)

    # ==========================================
    # ORDER BY PRIORITY
    # ==========================================

    query += """
        ORDER BY
            CASE lead_priority
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
                ELSE 4
            END,
            id
    """

    cursor.execute(query, parameters)

    leads = cursor.fetchall()

    connection.close()

    # ==========================================
    # FORMAT RESULTS
    # ==========================================

    results = []

    for lead in leads:

        results.append({

            "lead_id": lead[0],
            "name": lead[1],
            "email": lead[2],
            "priority": lead[3],
            "follow_up": lead[4],
            "timeframe": lead[5],
            "status": lead[6]

        })

    return jsonify({

        "count": len(results),
        "follow_ups": results

    }), 200
# ==========================================
# SEARCH LEADS
# ==========================================

@app.route("/leads/search", methods=["GET"])
@require_api_key
def search_leads():

    status = request.args.get("status")

    min_budget = request.args.get("min_budget")

    priority = request.args.get("priority")

    connection = sqlite3.connect("leads.db")

    cursor = connection.cursor()

    # ==========================================
    # BASE QUERY
    # ==========================================

    query = """
        SELECT
            lead_id,
            name,
            email,
            budget,
            status,
            lead_score,
            lead_priority
        FROM leads
        WHERE 1=1
    """

    parameters = []

    # ==========================================
    # FILTER BY STATUS
    # ==========================================

    if status:

        query += " AND status = ?"

        parameters.append(status)

    # ==========================================
    # FILTER BY MINIMUM BUDGET
    # ==========================================

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

    # ==========================================
    # FILTER BY PRIORITY
    # ==========================================

    if priority:

        allowed_priorities = [
            "LOW",
            "MEDIUM",
            "HIGH"
        ]

        priority = priority.upper()

        if priority not in allowed_priorities:

            connection.close()

            return jsonify({
                "error": "Invalid priority",
                "allowed_priorities": allowed_priorities
            }), 400

        query += " AND lead_priority = ?"

        parameters.append(priority)

    # ==========================================
    # ORDER RESULTS
    # ==========================================

    query += " ORDER BY id"

    cursor.execute(query, parameters)

    leads = cursor.fetchall()

    connection.close()

    # ==========================================
    # FORMAT RESULTS
    # ==========================================

    results = []

    for lead in leads:

        results.append({

            "lead_id": lead[0],
            "name": lead[1],
            "email": lead[2],
            "budget": lead[3],
            "status": lead[4],
            "lead_score": lead[5],
            "lead_priority": lead[6]

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