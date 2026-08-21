def qualify_lead(lead):

    reasons = []

    # VIP automatically qualifies
    if lead["vip_status"]:
        return True, ["VIP lead"]

    # Check qualification requirements

    if not lead["interested"]:
        reasons.append("Lead is not interested")

    if not lead["appointment_booked"]:
        reasons.append("Appointment not booked")

    if lead["budget"] < 50000:
        reasons.append("Budget below ₱50,000")

    if lead["age"] < 18:
        reasons.append("Lead is under 18")

    # No rejection reasons = qualified
    if not reasons:
        return True, []

    return False, reasons