def qualify_lead(lead):

    if lead["vip_status"]:
        return True

    if (
        lead["interested"]
        and lead["appointment_booked"]
        and lead["budget"] >= 50000
        and lead["age"] >= 18
    ):
        return True

    return False