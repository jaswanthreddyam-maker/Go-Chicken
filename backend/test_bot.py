import asyncio
import asyncpg
import json
import urllib.request
import time
import sys

URL = "http://localhost:8000/api/v1/whatsapp/webhook"

def send_msg(phone, text=None, button_id=None):
    if text:
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
                    "contacts": [{"profile": {"name": "Test User"}, "wa_id": phone}],
                    "messages": [msg]
                }
            }]
        }]
    }

    req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            print(f"Sent: {text or button_id} | Status: {res.status}")
    except Exception as e:
        print(f"Error sending {text or button_id}: {e}")

async def run_test():
    conn = await asyncpg.connect('postgresql://postgres:adminpassword@localhost:5435/go_chicken')
    phone = await conn.fetchval('SELECT phone FROM users LIMIT 1;')
    await conn.close()
    
    if not phone:
        print("No user found in DB.")
        return
        
    print(f"Testing with phone: {phone}")
    
    # Send Greeting
    send_msg(phone, text="hi")
    time.sleep(2)
    
    # Send Menu button (Place Order)
    send_msg(phone, button_id="menu_order")
    time.sleep(2)
    
    # Reply with Dressed product
    send_msg(phone, button_id="product_dressed")
    time.sleep(2)
    
    # Reply with quantity
    send_msg(phone, text="I want 50 kg please")
    time.sleep(2)
    
    # Click confirm
    send_msg(phone, button_id="confirm_order")
    time.sleep(2)
    
    # Test intent classification
    send_msg(phone, text="rate enti")
    time.sleep(2)
    
    print("Test finished. Check backend logs to see the bot replies.")

if __name__ == "__main__":
    asyncio.run(run_test())
