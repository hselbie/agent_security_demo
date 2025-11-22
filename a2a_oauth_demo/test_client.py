#!/usr/bin/env python3
"""Simple A2A client to test the orchestrator agent."""

import json
import requests
import uuid
from typing import Dict, Any

def send_message(agent_url: str, message: str, request_id: int = 1) -> Dict[str, Any]:
    """Send a message to the A2A agent using JSON-RPC."""
    url = agent_url  # RPC endpoint is at root /

    # A2A uses JSON-RPC 2.0 protocol
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": message
                    }
                ]
            }
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"\n📤 Sending: {message}")
    print(f"URL: {url}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        print(f"\n✅ Response:")
        print(json.dumps(result, indent=2))
        return result

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return {}

def main():
    """Main test function."""
    agent_url = "http://localhost:10007"

    print("=" * 60)
    print("A2A OAuth Demo Test Client")
    print("=" * 60)

    # Test 1: Simple greeting (should route to Greeter Agent)
    print("\n\n🧪 TEST 1: Greeting (Greeter Agent)")
    send_message(agent_url, "Hello", request_id=1)

    # Test 2: Calendar query (should route to Calendar Agent)
    print("\n\n🧪 TEST 2: Calendar Query (Calendar Agent)")
    send_message(agent_url, "Am I free from 10am to 11am tomorrow?", request_id=2)

if __name__ == "__main__":
    main()
