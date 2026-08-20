import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ==========================================
# SEND TELEGRAM NOTIFICATION
# ==========================================

def send_notification(lead):

    message = (
        "🚨 NEW QUALIFIED LEAD 🚨\n\n"
        f"👤 Name: {lead['name']}\n"
        f"📧 Email: {lead['email']}\n"
        f"💰 Budget: ₱{lead['budget']:,}\n"
        f"🆔 Lead ID: {lead['lead_id']}\n"
        f"📅 Appointment: "
        f"{'Booked' if lead['appointment_booked'] else 'Not booked'}\n"
        f"⭐ VIP: {'Yes' if lead['vip_status'] else 'No'}\n"
        f"🕐 Received: {lead['received_at']}\n"
        f"🎯 Status: {lead['status']}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:

        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=5
        )

        if response.status_code == 200:

            print("Telegram: Notification sent successfully")
            return "sent"

        else:

            print("Telegram ERROR:", response.status_code)
            print(response.text)
            return "failed"

    except requests.exceptions.RequestException as error:

        print("Telegram CONNECTION ERROR:", error)
        return "failed"