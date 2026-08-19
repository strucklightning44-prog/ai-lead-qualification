leads = [
    {
        "name": "Mark",
        "email": "mark@email.com",
        "budget": 75000,
        "interested": True,
        "vip_status": False,
        "age": 30,
        "appointment_booked": True
    },

    {
        "name": "John",
        "email": "john@email.com",
        "budget": 30000,
        "interested": True,
        "vip_status": False,
        "age": 25,
        "appointment_booked": True
    },

    {
        "name": "Sarah",
        "email": "sarah@email.com",
        "budget": 30000,
        "interested": True,
        "vip_status": True,
        "age": 40,
        "appointment_booked": True
    }
]


qualified_leads = []


for lead in leads:

    if lead["vip_status"] or (
        lead["interested"]
        and lead["appointment_booked"]
        and lead["budget"] >= 50000
        and lead["age"] >= 18
    ):
        lead["status"] = "qualified"
        qualified_leads.append(lead)

    else:
        lead["status"] = "not qualified"


print("QUALIFIED LEADS:")
print(qualified_leads)
import json
import requests

qualified_json = json.dumps(qualified_leads, indent=4)
url = "https://jsonplaceholder.typicode.com/posts"

for lead in qualified_leads:

    crm_lead = {
        "name": lead["name"],
        "email": lead["email"],
        "budget": lead["budget"],
        "status": lead["status"]
    }

    try:
        response = requests.post(url, json=crm_lead, timeout=5)

        if response.status_code == 201:
            print("SUCCESS:", lead["name"], "was sent.")
        else:
            print("ERROR:", lead["name"], "could not be sent.")
            print("Status code:", response.status_code)

    except requests.exceptions.RequestException as error:
        print("CONNECTION ERROR:", lead["name"])
        print("Details:", error)

    print("--------------------")