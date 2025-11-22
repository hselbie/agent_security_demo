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

1. Create the .env file with your API Key and OAuth2.0 Client details

   ```bash
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   echo "GOOGLE_CLIENT_ID=your_client_id_here" >> .env
   echo "GOOGLE_CLIENT_SECRET=your_client_secret_here" >> .env
   ```

2. Run the example

   ```bash
   uv run .
   ```

## Testing the agent

Try running the CLI host at `samples/python/hosts/cli` to interact with the agent.

```bash
uv run . --agent="http://localhost:10007"
```

### Test Case 1: Greeting (routed to Greeter Agent)
When prompted, type `Hello`. The orchestrator should route this to the greeter agent, which will respond with a simple greeting.

### Test Case 2: Calendar (routed to Calendar Agent)
When prompted, type `Am I free from 10am to 11am tomorrow?`. The orchestrator will route this to the calendar agent, which will trigger the OAuth flow. Follow the authentication URL in your browser to grant access.

### Test Case 3: Authenticated Calendar Request
To test providing pre-authentication to the agent, you can use `gcloud` to provide an ID token.

```bash
uv run . --agent="http://localhost:10007" --header="Authorization=Bearer $(gcloud auth print-identity-token)"
```
Now, when you ask a calendar-related question, the agent will use the identity from the token to authorize with the Google Calendar API.
