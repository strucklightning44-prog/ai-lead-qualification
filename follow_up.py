from datetime import datetime, timedelta


def create_follow_up(lead):

    priority = lead["lead_priority"]

    if priority == "HIGH":

        timeframe = "Within 15 minutes"
        minutes = 15

    elif priority == "MEDIUM":

        timeframe = "Within 1 hour"
        minutes = 60

    else:

        timeframe = "Within 24 hours"
        minutes = 1440

    due_time = datetime.now() + timedelta(minutes=minutes)

    return {

        "lead_id": lead["lead_id"],

        "action": "Contact lead",

        "priority": priority,

        "timeframe": timeframe,

        "due_at": due_time.isoformat(),

        "status": "pending"

    }