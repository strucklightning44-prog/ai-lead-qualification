import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

CRM_API_KEY = os.getenv("CRM_API_KEY")

def send_to_crm(lead):

    crm_lead = {
    "lead_id": lead["lead_id"],
    "name": lead["name"],
    "email": lead["email"],
    "budget": lead["budget"],
    "status": lead["status"],
    "lead_score": lead.get("lead_score", 0),
    "lead_priority": lead.get("lead_priority", "UNKNOWN")
}
    url = "https://jsonplaceholder.typicode.com/posts"
    for attempt in range(1, 4):

        try:

            print(f"CRM attempt {attempt}/3")

            response = requests.post(
                url,
                json=crm_lead,
                headers={
                    "Authorization": f"Bearer {CRM_API_KEY}"
                 },
                 timeout=5
               )

            if response.status_code in [200, 201]:

                print("CRM: Lead sent successfully")
                return "sent"

            elif response.status_code == 400:

                print("CRM ERROR: Bad request")
                return "failed"

            elif response.status_code == 401:

                print("CRM ERROR: Unauthorized")
                return "failed"

            elif response.status_code == 403:

                print("CRM ERROR: Forbidden")
                return "failed"

            elif response.status_code == 404:

                print("CRM ERROR: Endpoint not found")
                return "failed"

            elif response.status_code == 429 or response.status_code >= 500:

                print("CRM temporary error:", response.status_code)

                if attempt < 3:

                    wait_time = attempt
                    print(f"Retrying in {wait_time} second...")
                    time.sleep(wait_time)

                else:

                    print("CRM: All attempts failed")
                    return "failed"

            else:

                print(
                    "CRM ERROR: Unexpected status code",
                    response.status_code
                )
                return "failed"

        except requests.exceptions.Timeout:

            print("CRM ERROR: Request timed out")

            if attempt < 3:

                wait_time = attempt
                print(f"Retrying in {wait_time} second...")
                time.sleep(wait_time)

            else:

                print("CRM: All attempts failed")
                return "failed"

        except requests.exceptions.ConnectionError:

            print("CRM ERROR: Connection failed")

            if attempt < 3:

                wait_time = attempt
                print(f"Retrying in {wait_time} second...")
                time.sleep(wait_time)

            else:

                print("CRM: All attempts failed")
                return "failed"

        except requests.exceptions.RequestException as error:

            print("CRM ERROR:", error)
            return "failed"