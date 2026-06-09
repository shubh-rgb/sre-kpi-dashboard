import os
import requests

api_key = os.getenv("FRESHSERVICE_API_KEY")
domain = os.getenv("FRESHSERVICE_DOMAIN")

if not api_key:
    print("Error: FRESHSERVICE_API_KEY environment variable not set")
    exit(1)

if not domain:
    print("Error: FRESHSERVICE_DOMAIN environment variable not set")
    exit(1)

headers = {
    "Authorization": f"Basic {api_key}"
}

response = requests.get(
    f"https://{domain}.freshservice.com/api/v2/tickets",
    headers=headers
)