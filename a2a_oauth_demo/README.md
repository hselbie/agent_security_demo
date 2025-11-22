# ADK Multi-Agent with an Orchestrator

This example shows how to create an A2A Server that uses an ADK-based orchestrator agent to route requests to sub-agents with different capabilities, including one that uses Google-authenticated tools.

The orchestrator agent decides which sub-agent to use based on the user's prompt. The sub-agents in this example are:
- **Greeter Agent**: A simple agent that responds to greetings.
- **Calendar Agent**: An agent that can access a user's Google Calendar and requires OAuth2 authentication.

This example also demonstrates server-side authentication. If an incoming request contains a JWT, the agent will associate the Calendar API authorization with the `sub` of the token and reuse it for future requests from the same user.

## Prerequisites

- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/)
- A Gemini API Key
- A [Google OAuth Client](https://developers.google.com/identity/openid-connect/openid-connect#getcredentials)
  - Configure your OAuth client to handle redirect URLs at `localhost:10007/authenticate`

## Running the example

1. Ensure your `.env` file is configured at the **project root** (`../../.env`) with your Gemini API Key or Vertex AI configuration, and your Google OAuth Client details. Refer to the root `/.env_example` for the correct format.

2. Run the example

   ```bash
   uv run .
   ```

## Testing the agent

Use the provided test client to interact with the A2A agent:

```bash
python3 test_client.py
```

The test client demonstrates two scenarios:

### Test Case 1: Greeting (routed to Greeter Agent)
Sends "Hello" to the orchestrator, which should route this to the greeter agent for a simple greeting response.

### Test Case 2: Calendar Query (routed to Calendar Agent)
Sends "Am I free from 10am to 11am tomorrow?" to the orchestrator, which routes it to the calendar agent. This will trigger the OAuth flow, providing an authorization URL in the response. Follow the authentication URL in your browser to grant calendar access.

### Test Case 3: Authenticated Calendar Request
To test providing pre-authentication to the agent, you can send requests with a JWT token. Modify the test client to include an Authorization header:

```python
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {your_id_token}"
}
```

Or use curl with gcloud:
```bash
curl -X POST http://localhost:10007/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -d '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"kind":"message","messageId":"test-123","role":"user","parts":[{"kind":"text","text":"Am I free tomorrow at 10am?"}]}}}'
```

When you provide a valid ID token, the agent will associate the Calendar API authorization with the `sub` claim from the token and reuse it for future requests from the same user.
