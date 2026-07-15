"""Simulated WhatsApp to n8n Webhook Trigger Script for Hackathon Demo.

Allows instant simulation of WhatsApp messages and interactive button clicks
sending payloads directly to the active n8n webhook (or local test webhook).

Usage:
    python -m scripts.simulate_whatsapp_n8n
    OR
    python scripts/simulate_whatsapp_n8n.py
"""

import argparse
import json
import logging
import sys
import time
import urllib.request
from urllib.error import HTTPError, URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("go_chicken.simulate_n8n")

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/whatsapp"
N8N_TEST_WEBHOOK_URL = "http://localhost:5678/webhook-test/whatsapp"


def send_to_n8n(payload: dict, use_test_webhook: bool = False, custom_url: str = None) -> dict:
    url = custom_url if custom_url else (N8N_TEST_WEBHOOK_URL if use_test_webhook else N8N_WEBHOOK_URL)
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "Meta-WhatsApp-Cloud-API/1.0"},
        method="POST",
    )

    try:
        logger.info(f"📤 Dispatching simulated WhatsApp payload to n8n -> {url}...")
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            logger.info(f"✅ n8n responded with status {response.status}")
            try:
                return json.loads(res_body)
            except json.JSONDecodeError:
                return {"raw_response": res_body}
    except HTTPError as e:
        logger.error(f"❌ n8n Webhook HTTP Error: {e.code} - {e.reason}")
        error_content = e.read().decode("utf-8", errors="ignore")
        if e.code == 404:
            logger.warning(
                "\n💡 NOTE: A 404 error means the n8n webhook URL is not active yet.\n"
                "Please open http://localhost:5678 in your browser, import `workflows/n8n_whatsapp_orchestration.json`,\n"
                "and click the 'Active' toggle in the top right corner (or click 'Test workflow' if using --test)."
            )
        return {"error": e.code, "details": error_content}
    except URLError as e:
        logger.error(f"❌ Could not connect to n8n at {url}: {e.reason}")
        logger.warning("Please ensure your n8n Docker container is running (`docker ps`).")
        return {"error": str(e)}


def create_text_message_payload(phone: str, text: str) -> dict:
    """Creates a realistic Meta WhatsApp Cloud API text message payload."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1023464150604430",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "+1 555 170 1265", "phone_number_id": "1245784945278928"},
                            "contacts": [{"profile": {"name": "Raju Chicken Center"}, "wa_id": phone}],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": f"wamid.HBgL{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": text},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
        # Direct convenience shortcut parsed by our code node as well
        "phone": phone,
        "message": text,
    }


def create_button_reply_payload(phone: str, button_id: str, button_title: str) -> dict:
    """Creates a realistic Meta WhatsApp Cloud API interactive button reply payload."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1023464150604430",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "+1 555 170 1265", "phone_number_id": "1245784945278928"},
                            "contacts": [{"profile": {"name": "Raju Chicken Center"}, "wa_id": phone}],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": f"wamid.HBgL{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {"id": button_id, "title": button_title},
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
        "phone": phone,
        "button_id": button_id,
        "message": button_title,
    }


def main():
    parser = argparse.ArgumentParser(description="Simulate WhatsApp messages directly to n8n.")
    parser.add_argument("--test", action="store_true", help="Use n8n test webhook URL (/webhook-test/whatsapp)")
    parser.add_argument("--url", help="Custom n8n webhook URL (overrides default/test URLs)")
    parser.add_argument("--phone", default="919876543211", help="Sender WhatsApp number (default: Raju Chicken Center)")
    parser.add_argument("--message", default="50kg live bird", help="Text message body to send")
    parser.add_argument("--confirm", help="Order UUID to send a simulated 'Confirm Order' button click for")
    parser.add_argument("--cancel", help="Order UUID to send a simulated 'Cancel Order' button click for")

    args = parser.parse_args()

    print("==================================================================")
    print("GO CHICKEN - WHATSAPP TO N8N WEBHOOK SIMULATOR")
    print("==================================================================")

    if args.confirm:
        payload = create_button_reply_payload(args.phone, f"confirm_order_{args.confirm}", "Confirm Order")
        logger.info(f"Simulating interactive button click: Confirm Order #{args.confirm}")
    elif args.cancel:
        payload = create_button_reply_payload(args.phone, f"cancel_order_{args.cancel}", "Cancel Order")
        logger.info(f"Simulating interactive button click: Cancel Order #{args.cancel}")
    else:
        payload = create_text_message_payload(args.phone, args.message)
        logger.info(f"Simulating text message from {args.phone}: '{args.message}'")

    response = send_to_n8n(payload, use_test_webhook=args.test, custom_url=args.url)
    print("\n[Response from n8n]:")
    print(json.dumps(response, indent=2))
    print("==================================================================")


if __name__ == "__main__":
    main()
