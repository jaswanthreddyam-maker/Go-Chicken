import time
import requests
import json
import uuid

WEBHOOK_URL = "http://localhost:8000/api/v1/whatsapp/webhook"

# A delay to allow the browser subagent to log in and reach the dashboard
print("Waiting 15 seconds before simulating WhatsApp order...")
time.sleep(15)

def send_webhook(body):
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "test_business_account",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "test_phone_id"
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Test Retailer"},
                                    "wa_id": "1234567890"
                                }
                            ],
                            "messages": [body]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    print(f"Sending webhook: {json.dumps(payload)}")
    try:
        res = requests.post(WEBHOOK_URL, json=payload)
        print(f"Response: {res.status_code} {res.text}")
    except Exception as e:
        print(f"Failed to send webhook: {e}")

# 1. Send natural language order
msg_order = {
    "from": "1234567890",
    "id": str(uuid.uuid4()),
    "timestamp": str(int(time.time())),
    "type": "text",
    "text": {"body": "I need 50kg live bird tomorrow morning"}
}
send_webhook(msg_order)

# Wait 5 seconds for AI to process and return quote
time.sleep(5)

# 2. Accept quote (simulate button click)
msg_accept = {
    "from": "1234567890",
    "id": str(uuid.uuid4()),
    "timestamp": str(int(time.time())),
    "type": "interactive",
    "interactive": {
        "type": "button_reply",
        "button_reply": {
            "id": "accept_quote",
            "title": "Confirm Order"
        }
    }
}
send_webhook(msg_accept)

print("WhatsApp simulation complete.")
