import json
from lead import Lead
# ==========================================
# STEP 1 — CREATE OUR LEADS
# ==========================================
lead1 = Lead(
    "Mark",
    "mark@email.com",
    150000,
    True,
    True)
lead2 = Lead(
    "John",
    "john@email.com",
    50000,
    True,
    True)
lead3 = Lead(
    "Sarah",
    "sarah@email.com",
    200000,
    False,
    True)
# ==========================================
# STEP 2 — PUT ALL LEADS INTO ONE LIST
# ==========================================
leads = [lead1, lead2, lead3]
# ==========================================
# STEP 3 — PROCESS EACH LEAD
# ==========================================
for lead in leads:
    print("\n==============================")
    print("Processing:", lead.name)
    print("==============================")
    # --------------------------------------
    # Ask the Lead object to qualify itself.
    #
    # qualify() gives us two things:
    #
    # result
    # reasons
    # --------------------------------------
    result, reasons = lead.qualify()
    # --------------------------------------
    # Create a dictionary containing
    # everything we want to save.
    # --------------------------------------
    lead_data = {
        "name": lead.name,
        "email": lead.email,
        "budget": lead.budget,
        "appointment_booked": lead.appointment_booked,
        "interested": lead.interested,
        "result": result,
        "reasons": reasons 
        }
    # --------------------------------------
    # Convert the Python dictionary into JSON.
    #
    # JSON is useful because APIs and
    # automation systems commonly use it
    # to exchange information.
    # --------------------------------------
    lead_json = json.dumps(lead_data, indent=4)
    # --------------------------------------
    # Display the JSON.
    # --------------------------------------
    print(lead_json)
    # --------------------------------------
    # Show each reason separately.
    # --------------------------------------
    print("\nReasons:")
    for reason in reasons:
        print("-", reason)
    # --------------------------------------
    # Decide what the automation should do.
    # --------------------------------------
    if result == "Qualified Lead":
        print("\nACTION: Send this lead to CRM")
    else:
        print("\nACTION: Send follow-up message")