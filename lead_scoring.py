def calculate_lead_score(lead):

    score = 0

    # VIP lead
    if lead["vip_status"]:
        score += 50

    # Budget
    if lead["budget"] >= 500000:
        score += 30

    elif lead["budget"] >= 100000:
        score += 20

    elif lead["budget"] >= 50000:
        score += 10

    # Appointment
    if lead["appointment_booked"]:
        score += 20

    # Interest
    if lead["interested"]:
        score += 10

    # Age
    if lead["age"] >= 25:
        score += 5

    return min(score,100)
def get_lead_priority(score):

    if score >= 80:
        return "HIGH"

    elif score >= 50:
        return "MEDIUM"

    else:
        return "LOW"
