import requests


# ==========================================
# SEND LEAD TO CRM
# ==========================================

def send_to_crm(lead):

    crm_lead = {
        "lead_id": lead["lead_id"],
        "name": lead["name"],
        "email": lead["email"],
        "budget": lead["budget"],
        "status": lead["status"]
    }

    url = "https://jsonplaceholder.typicode.com/posts"

    try:

        response = requests.post(
            url,
            json=crm_lead,
            timeout=5
        )

        if response.status_code == 201:

            print("CRM: Lead sent successfully")
            return "sent"

        else:

            print("CRM ERROR:", response.status_code)
            return "failed"

    except requests.exceptions.RequestException as error:

        print("CONNECTION ERROR:", error)
        return "failed"