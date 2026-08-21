import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ==========================================
# SEND TELEGRAM NOTIFICATION
# ==========================================

def send_notification(lead):

    if lead.get("notification_type") == "crm_failed":
        title = "🔴 CRM FAILED - ACTION REQUIRED 🔴"

    elif lead["status"] == "qualified":
        title = "🚨 NEW QUALIFIED LEAD 🚨"

    else:
        title = "⚠️ NEW UNQUALIFIED LEAD ⚠️"
    reasons_text = ""

    if lead.get("qualification_reasons"):

        reasons_text = "\n❌ Reasons:\n"

        for reason in lead["qualification_reasons"]:
            reasons_text += f"• {reason}\n"
    message = (
        f"{title}\n\n"
        f"👤 Name: {lead['name']}\n"
        f"📧 Email: {lead['email']}\n"
        f"💰 Budget: ₱{lead['budget']:,}\n"
        f"🆔 Lead ID: {lead['lead_id']}\n"
        f"📅 Appointment: "
        f"{'Booked' if lead['appointment_booked'] else 'Not booked'}\n"
        f"⭐ VIP: {'Yes' if lead['vip_status'] else 'No'}\n"
        f"🕐 Received: {lead['received_at']}\n"
        f"🎯 Status: {lead['status']}\n"
        f"📊 Lead Score: {lead.get('lead_score', 0)}/100\n"
        f"🎯 Priority: {lead.get('lead_priority', 'UNKNOWN')}"
        f"{reasons_text}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    for attempt in range(1, 4):

        try:

            print(f"Telegram attempt {attempt}/3")

            response = requests.post(
                url,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message
                },
                timeout=20
            )

            if response.status_code == 200:

                print("Telegram: Notification sent successfully")
                return "sent"

            else:

                print("Telegram ERROR:", response.status_code)
                print(response.text)

                if attempt < 3:

                    wait_time = attempt

                    print(
                        f"Retrying Telegram in {wait_time} second..."
                    )

                    time.sleep(wait_time)

                else:

                    print("Telegram: All attempts failed")
                    return "failed"

        except requests.exceptions.RequestException as error:

            print("Telegram CONNECTION ERROR:", error)

            if attempt < 3:

                wait_time = attempt

                print(
                    f"Retrying Telegram in {wait_time} second..."
                )

                time.sleep(wait_time)

            else:

                print("Telegram: All attempts failed")
                return "failed"