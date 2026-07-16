import asyncio
import json
import urllib.request
import time
import sys
import argparse

URL = "http://127.0.0.1:8000/api/v1/whatsapp/webhook"

def send_msg(phone, name="Test Retailer", text=None, button_id=None, lat=None, lon=None):
    if lat and lon:
        msg = {
            "from": phone,
            "id": f"wamid.{int(time.time())}",
            "timestamp": str(int(time.time())),
            "type": "location",
            "location": {
                "latitude": lat,
                "longitude": lon,
                "name": "Shop Location",
                "address": "Hyderabad"
            }
        }
    elif text:
        msg = {
            "from": phone,
            "id": f"wamid.{int(time.time())}",
            "timestamp": str(int(time.time())),
            "type": "text",
            "text": {"body": text}
        }
    else:
        msg = {
            "from": phone,
            "id": f"wamid.{int(time.time())}",
            "timestamp": str(int(time.time())),
            "type": "interactive",
            "interactive": {
                "type": "button_reply",
                "button_reply": {"id": button_id, "title": "Btn"}
            }
        }

    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "1234567890",
                        "phone_number_id": "10101010"
                    },
                    "contacts": [{"profile": {"name": name}, "wa_id": phone}],
                    "messages": [msg]
                }
            }]
        }]
    }

    req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            action = text or button_id or "Location"
            print(f"Sent: {action} | Status: {res.status}")
    except Exception as e:
        action = text or button_id or "Location"
        print(f"Error sending {action}: {e}")

async def run_test(phone, invite_code):
    print(f"Starting Onboarding Simulation for: {phone}")
    
    print("\n--- STEP 1: Scan QR Code ---")
    send_msg(phone, text=f"JOIN_GC_{invite_code}")
    time.sleep(2)
    
    print("\n--- STEP 2: Select Language ---")
    send_msg(phone, button_id="lang_en")
    time.sleep(2)
    
    print("\n--- STEP 3: Enter Name ---")
    send_msg(phone, text="Ravi Kumar")
    time.sleep(2)
    
    print("\n--- STEP 4: Share Location ---")
    send_msg(phone, lat=17.385044, lon=78.486671)
    time.sleep(2)
    
    print("\n--- STEP 5: Enter Shop Name ---")
    send_msg(phone, text="Ravi Chicken Center")
    time.sleep(2)
    
    print("\n--- STEP 6: Confirm ---")
    send_msg(phone, button_id="btn_confirm")
    time.sleep(2)
    
    print("\nTest finished! Check your Go Chicken dashboard under the Retailers tab.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test WhatsApp Onboarding Flow')
    parser.add_argument('--phone', type=str, required=True, help='Phone number without + (e.g. 919876543210)')
    parser.add_argument('--invite', type=str, required=True, help='Invite code generated from Dashboard (e.g. XYZ123)')
    args = parser.parse_args()
    
    asyncio.run(run_test(args.phone, args.invite))
