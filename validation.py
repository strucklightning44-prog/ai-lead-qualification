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