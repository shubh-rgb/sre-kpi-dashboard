"""
Freshservice API integration for fetching ticket and incident data
"""
import os
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path

FRESHSERVICE_API_KEY = os.getenv("FRESHSERVICE_API_KEY", "")
FRESHSERVICE_DOMAIN = os.getenv("FRESHSERVICE_DOMAIN", "")
BASE_URL = f"https://{FRESHSERVICE_DOMAIN}.freshservice.com/api/v2"


class FreshserviceClient:
    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain
        self.base_url = f"https://{domain}.freshservice.com/api/v2"
        self.session = requests.Session()
        self.session.auth = (api_key, "X")
        self.session.headers.update({"Content-Type": "application/json"})

    def _make_request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None):
        """Make API request to Freshservice"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(method, url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Freshservice API error: {e}")
            return None

    def get_tickets(self, page: int = 1, per_page: int = 100) -> Optional[Dict]:
        """Fetch tickets from Freshservice"""
        return self._make_request("tickets", params={"page": page, "per_page": per_page})

    def get_incidents(self, page: int = 1, per_page: int = 100) -> Optional[Dict]:
        """Fetch incidents from Freshservice"""
        return self._make_request("incidents", params={"page": page, "per_page": per_page})

    def get_problems(self, page: int = 1, per_page: int = 100) -> Optional[Dict]:
        """Fetch problems from Freshservice"""
        return self._make_request("problems", params={"page": page, "per_page": per_page})

    def get_changes(self, page: int = 1, per_page: int = 100) -> Optional[Dict]:
        """Fetch change requests from Freshservice"""
        return self._make_request("changes", params={"page": page, "per_page": per_page})


def fetch_freshservice_data() -> List[Dict]:
    """
    Fetch data from Freshservice and return as list of records
    """
    if not FRESHSERVICE_API_KEY or not FRESHSERVICE_DOMAIN:
        print("Warning: FRESHSERVICE_API_KEY or FRESHSERVICE_DOMAIN not configured")
        return []

    client = FreshserviceClient(FRESHSERVICE_API_KEY, FRESHSERVICE_DOMAIN)
    records = []

    # Fetch tickets
    print("Fetching Freshservice tickets...")
    tickets_data = client.get_tickets()
    if tickets_data and "tickets" in tickets_data:
        for ticket in tickets_data["tickets"]:
            record = {
                "id": ticket.get("id"),
                "type": "ticket",
                "subject": ticket.get("subject"),
                "description": ticket.get("description", ""),
                "status": ticket.get("status"),
                "priority": ticket.get("priority"),
                "requester_id": ticket.get("requester_id"),
                "assigned_to_id": ticket.get("responder_id"),
                "created_at": ticket.get("created_at"),
                "updated_at": ticket.get("updated_at"),
                "resolved_at": ticket.get("resolved_at"),
            }
            records.append(record)

    # Fetch incidents
    print("Fetching Freshservice incidents...")
    incidents_data = client.get_incidents()
    if incidents_data and "incidents" in incidents_data:
        for incident in incidents_data["incidents"]:
            record = {
                "id": incident.get("id"),
                "type": "incident",
                "subject": incident.get("subject"),
                "description": incident.get("description", ""),
                "status": incident.get("status"),
                "priority": incident.get("priority"),
                "requester_id": incident.get("requester_id"),
                "assigned_to_id": incident.get("responder_id"),
                "created_at": incident.get("created_at"),
                "updated_at": incident.get("updated_at"),
                "resolved_at": incident.get("resolved_at"),
            }
            records.append(record)

    print(f"Fetched {len(records)} total records from Freshservice")
    return records


def save_freshservice_csv(records: List[Dict], output_path: Path):
    """Save fetched Freshservice data to CSV"""
    if not records:
        print("No records to save")
        return

    import csv

    csv_path = output_path / "freshservice_data.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(f"Saved {len(records)} records to {csv_path}")
