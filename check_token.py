#!/usr/bin/env python3
"""Check what accounts the new token has access to."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HF_TOKEN")
headers = {"Authorization": f"Bearer {token}"}

# Get user info
print("Getting user info...")
response = requests.get("https://api.huntflow.ru/v2/me", headers=headers)
if response.status_code == 200:
    user_data = response.json()
    print(f"User: {user_data.get('name', 'Unknown')}")
    print(f"Email: {user_data.get('email', 'Unknown')}")
else:
    print(f"Error getting user info: {response.status_code} - {response.text}")

# Get accounts
print("\nGetting accounts...")
response = requests.get("https://api.huntflow.ru/v2/accounts", headers=headers)
if response.status_code == 200:
    accounts = response.json()
    print(f"\nAvailable accounts:")
    for account in accounts.get("items", []):
        print(f"- ID: {account['id']}, Name: {account['name']}")
        
        # Try to get vacancy statuses for this account
        status_response = requests.get(
            f"https://api.huntflow.ru/v2/accounts/{account['id']}/vacancies/statuses", 
            headers=headers
        )
        if status_response.status_code == 200:
            print(f"  ✓ Has access to vacancy statuses")
        else:
            print(f"  ✗ No access to vacancy statuses: {status_response.status_code}")
else:
    print(f"Error getting accounts: {response.status_code} - {response.text}")