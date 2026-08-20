import json


COUNTER_FILE = "counter.json"


def load_counter():

    with open(COUNTER_FILE, "r") as file:
        counter_data = json.load(file)

    return counter_data["last_lead_id"]


def generate_lead_id():

    current_counter = load_counter()

    current_counter += 1

    with open(COUNTER_FILE, "w") as file:
        json.dump({
            "last_lead_id": current_counter
        }, file)

    return f"LEAD-{current_counter:03d}"