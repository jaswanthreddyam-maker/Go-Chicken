import urllib.request
import json
import subprocess
import sys
import random

INVITE_URL = "http://127.0.0.1:8000/api/v1/retailers/invite"

def main():
    print("1. Generating Invitation...")
    req = urllib.request.Request(
        INVITE_URL,
        data=json.dumps({}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            invite_code = data["invite_code"]
            print(f"   Success! Invite Code: {invite_code}")
    except Exception as e:
        print(f"Error generating invite: {e}")
        sys.exit(1)

    phone = f"9198{random.randint(10000000, 99999999)}"
    print(f"\n2. Running Simulation with phone: {phone}")
    
    subprocess.run([
        sys.executable,
        "scripts/test_onboarding.py",
        "--phone", phone,
        "--invite", invite_code
    ])

if __name__ == "__main__":
    main()
