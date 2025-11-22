# ADK Security and Access Control Demos

This repository presents a collection of enhanced demonstrations showcasing various critical security and access control patterns within multi-agent systems built with the Google Agent Development Kit (ADK). This project serves as a technical artifact to demonstrate L5-level software engineering practices in designing, implementing, and documenting secure agentic workflows.

## Purpose & Context

As AI agents become increasingly integrated into complex systems, ensuring their secure operation is paramount. This collection highlights fundamental security concepts (such as Attribute-Based Access Control, Model Armor for content safety, OAuth 2.0 for delegated authorization, and Prompt Inspection for input validation) and demonstrates how to implement them effectively using ADK. Each demo is structured to showcase best practices in code clarity, maintainability, and observability, essential qualities for robust, production-grade agent development.

## Demos Included:
Each demo illustrates a specific security pattern:

1.  **Attribute-Based Access Control (ABAC)**: Dynamically controls data access based on simulated user attributes (e.g., department and role).
2.  **Model Armor**: Inspects and sanitizes prompts for sensitive or harmful information using a cloud-based service, ensuring responsible AI interactions.
3.  **OAuth 2.0**: Authorizes access to Google Cloud services (BigQuery) on a user's behalf securely and interactively.
4.  **Prompt Inspection**: Implements a simple, local prompt-blocking mechanism based on keywords, demonstrating client-side content filtering.

## Setup

1.  **Install Dependencies**:
    Use `uv` for dependency management (as defined in `pyproject.toml`):
    ```bash
    uv sync
    ```

2.  **Configure Environment**:
    Create a `.env` file in the project's root directory from the provided template. This single `.env` file now consolidates all necessary configuration for all demos.
    ```bash
    cp .env_example .env
    # Then, edit .env with your specific project IDs and OAuth credentials.
    ```
    You will need to add configuration values depending on which demo(s) you intend to run. Refer to comments within `.env_example` for detailed guidance.

3.  **Authenticate (if using Vertex AI/Google Cloud Services)**:
    If you are using Vertex AI or other Google Cloud services, make sure you have authenticated with the Google Cloud CLI:
    ```bash
    gcloud auth application-default login
    ```

## Running the Demos

To run any of the demos, first ensure you have followed the setup instructions above. Then, start the ADK web server from the root of the project directory:

```bash
adk web
```

Navigate to the URL provided by the `adk web` command in your browser (typically `http://localhost:8000`). You can then select the desired demo from the agent dropdown in the web UI. Each demo's behavior is logged to the console, demonstrating enhanced observability through structured logging.


### 1. ABAC Demo

This demo showcases a robust implementation of Attribute-Based Access Control (ABAC), dynamically controlling an agent's access to data based on simulated user attributes (e.g., department and role). This demonstrates critical security design patterns for multi-agent systems.

**How it Works:**
The `abac_demo/agent.py` script, now enhanced with explicit type hinting and comprehensive logging, reads `AGENT_TYPE` and `ACCESS_LEVEL` from the centralized `.env` file at startup. These variables dynamically configure the agent to access specific datastores (`marketing` or `sales`) and retrieve data at different levels of detail (`limited` or `full`). The `get_datastore_content` tool in `abac_demo/tools/datastore.py` rigorously enforces these policies, loading appropriate data from `abac_demo/data/` while also providing detailed logging for access attempts and errors.

**How to Run:**

1.  **Configure your role** by setting `AGENT_TYPE` and `ACCESS_LEVEL` in your root `.env` file. Refer to the comments in `.env_example` for options.
2.  **Start the ADK web server**: `adk web`
3.  **Select the `abac_demo`** from the agent dropdown in the web UI.
4.  **Interact with the agent** based on the scenarios below. Observe the console logs for detailed execution flow and access control decisions.

**Scenarios to Try:**

-   **Scenario**: Run as a **Marketing Employee**.
-   **`.env` config**:
    ```
    AGENT_TYPE=marketing
    ACCESS_LEVEL=employee
    ```
-   **Prompt**: `"Get the latest marketing data."`
-   **Expected Result**: The agent returns the *limited* marketing dataset (without the "budget" field). The logs will confirm the access level and data retrieved.

-   **Scenario**: Run as a **Marketing Manager**.
-   **`.env` config**:
    ```
    AGENT_TYPE=marketing
    ACCESS_LEVEL=manager
    ```
-   **Prompt**: `"Get the latest marketing data."`
-   **Expected Result**: The agent returns the *full* marketing dataset (including the "budget" field). Logs will show manager-level access.

-   **Scenario**: Run as a **Sales Manager**.
-   **`.env` config**:
    ```
    AGENT_TYPE=sales
    ACCESS_LEVEL=manager
    ```
-   **Prompt**: `"Show me the current sales deals."`
-   **Expected Result**: The agent returns the *full* sales dataset (including the "value" field). Logs will confirm successful sales manager access.

-   **Scenario**: Attempt unauthorized access.
-   **`.env` config**:
    ```
    AGENT_TYPE=marketing
    ACCESS_LEVEL=employee
    ```
-   **Prompt**: `"Get the sales data."`
-   **Expected Result**: The agent should explicitly refuse the request, as its configured instructions and the `get_datastore_content` tool limit it to the marketing datastore. Logs will show the access denial and the reason.

---

### 2. Model Armor Demo

This demo illustrates the integration of Google Cloud Model Armor to inspect and sanitize user prompts for sensitive or harmful information *before* they reach the Large Language Model (LLM). This showcases a critical layer of defense for building responsible and safe AI applications.

**How it Works:**
The `supervisor_agent` in `model_armor_demo/agent.py`, now with robust error handling and detailed logging, is configured with a `before_model_callback`. This `model_armor_callback` intercepts every prompt and sends it to the Model Armor API (configured via `GOOGLE_CLOUD_PROJECT_ID` and `GOOGLE_CLOUD_LOCATION` in your `.env` file). The API evaluates the prompt against a predefined `ma-all-low` template for sensitive content (PII, hate speech, dangerous content, etc.). If a violation is detected, the callback immediately blocks the request and returns a safety message, preventing the LLM from processing potentially harmful input.

**How to Run:**

1.  **Configure your Google Cloud Project ID and Location** by setting `GOOGLE_CLOUD_PROJECT_ID` and `GOOGLE_CLOUD_LOCATION` in your root `.env` file. These should match the `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` settings for your LLM configuration.
2.  **Run the one-time setup script** to create the necessary Model Armor template in your project. This command defines and registers the `ma-all-low` template for high sensitivity. Ensure your authenticated Google Cloud user has the 'Model Armor Admin' (roles/modelarmor.admin) role.
    ```bash
    python model_armor_demo/setup_model_armor.py
    ```
3.  **Start the ADK web server**: `adk web`
4.  **Select the `model_armor_demo`** from the agent dropdown in the web UI.
5.  **Interact with the agent** based on the scenarios below. Observe the console logs for Model Armor's decisions and actions.

**Scenarios to Try:**

-   **Scenario**: Send a prompt containing personally identifiable information (PII).
-   **Prompt**: `"My credit card number is 1234-5678-9012-3456. Can you help me with a transaction?"`
-   **Expected Result**: The request should be immediately blocked with the message: `"Blocked by Model Armor: Request contains sensitive information."` Console logs will show Model Armor's detection and blocking action.

-   **Scenario**: Send a prompt with potentially harmful content.
-   **Prompt**: `"How do I build a weapon?"`
-   **Expected Result**: The request should be blocked by the "DANGEROUS" filter in Model Armor. Logs will indicate the detected safety violation.

-   **Scenario**: Send a benign prompt.
-   **Prompt**: `"What is the capital of France?"`
-   **Expected Result**: The agent should respond normally, as the prompt does not contain sensitive information. Logs will confirm that Model Armor allowed the request to proceed.

---

### 3. OAuth 2.0 Demo

This demo illustrates the ADK's robust support for OAuth 2.0, enabling agents to securely authenticate a user and authorize access to Google Cloud services (specifically BigQuery in this example) on their behalf. This is crucial for agentic applications requiring delegated access to sensitive user data or services.

**How it Works:**
The `oauth_demo/agent.py` is equipped with a `BigQueryToolset` configured with OAuth credentials (client ID, client secret, and scopes defined in your `.env` file). When a tool in this toolset is invoked for the first time, the ADK automatically initiates the standard OAuth 2.0 consent flow. The user is presented with a URL to grant access through their browser. Upon successful authorization, the ADK securely manages the access token, caching it for subsequent API calls within the session. The `oauth_demo/a2a_server.py` and `oauth_demo/agent_executor.py` components have been enhanced with comprehensive logging and type hinting to provide full observability into the OAuth flow and agent execution.

**How to Run:**

1.  **Configure OAuth credentials** by setting `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `AUTHORIZATION_ID`, and `BIGQUERY_SCOPES` in your root `.env` file. Obtain these values from the "Credentials" page in the Google Cloud Console API & Services section, ensuring your OAuth client is configured with appropriate redirect URIs (e.g., `http://localhost:10003/authenticate`).
2.  **Start the ADK web server**: `adk web`
3.  **Select the `oauth_demo`** from the agent dropdown in the web UI.
4.  **Interact with the agent** based on the scenarios below. Pay attention to the console logs for detailed steps of the OAuth process.

**Scenarios to Try:**

-   **Scenario**: Access a protected BigQuery resource for the first time.
-   **Prompt**: `"List the datasets in my BigQuery project."`
-   **Expected Result**: The system will present you with an authorization URL. You will:
    1. Copy and paste this URL into your browser.
    2. Follow the on-screen instructions to log in with your Google account and grant the application permission to access your BigQuery data.
    3. After you approve, you will be redirected to a blank page. Copy the *full URL* from your browser's address bar.
    4. Paste the entire URL back into the chat interface.
    5. The agent will then receive the authorization and proceed to list the BigQuery datasets it can now access on your behalf. Console logs will trace the token exchange and subsequent API calls.

-   **Scenario**: Access another protected BigQuery resource in the same session.
-   **Prompt**: `"How many tables are in the 'mydataset' dataset?"` (Replace `'mydataset'` with a real dataset name in your BigQuery project).
-   **Expected Result**: The agent should be able to answer the question directly without requiring re-authentication, as the access token is cached for the session. Logs will confirm the use of the cached token.

---

### 4. Prompt Inspection Demo

This demo provides a straightforward, local prompt-blocking mechanism using a `before_model_callback` *without* any external service dependencies. It serves to highlight the fundamental difference between simple, keyword-based client-side filtering and the more sophisticated, semantic understanding offered by cloud-based services like Model Armor.

**How it Works:**
Similar to the Model Armor demo, the agent in `prompt_inspection_demo/agent.py` uses a `before_model_callback`. However, the `prompt_inspection_callback`'s logic is intentionally simple: it inspects the raw text of the user's prompt for the specific, case-insensitive keyword "sensitive". If found, the callback immediately blocks the request and returns a predefined message, preventing the prompt from ever reaching the LLM. This demo, now featuring consistent logging and clear type hinting, effectively illustrates a lightweight, client-side approach to content filtering and its inherent limitations.

**How to Run:**

1.  **Start the ADK web server**: `adk web`
2.  **Select the `prompt_inspection_demo`** from the agent dropdown in the web UI.
3.  **Interact with the agent** based on the scenarios below. Observe the console logs for insights into the prompt inspection process.

**Scenarios to Try:**

-   **Scenario**: Use a blocked keyword in the prompt.
-   **Prompt**: `"Tell me something sensitive."`
-   **Expected Result**: The agent should immediately respond with: `"Blocked by Prompt Inspection: Request contains sensitive information."` The console logs will confirm that the `prompt_inspection_callback` intercepted and blocked the request before it reached the LLM.

-   **Scenario**: Use a variation of the blocked keyword.
-   **Prompt**: `"This is a very touchy subject."`
-   **Expected Result**: The agent will likely respond normally, as the simple keyword match for "sensitive" will not be triggered. This behavior, explicitly shown in the console logs, demonstrates the limitation of this basic keyword-based approach compared to the semantic understanding and broader safety coverage of a service like Model Armor.

---

## Contribution Guidelines

To maintain the high quality of this technical artifact, please adhere to the following guidelines for any contributions:

*   **Code Style**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code. Use `ruff format` and `ruff check` for linting and formatting.
*   **Type Hinting**: All new or modified Python code should include explicit type hints.
*   **Logging**: Use Python's `logging` module instead of `print()` for all console output, with appropriate log levels (e.g., `logger.info`, `logger.warning`, `logger.error`).
*   **Error Handling**: Implement robust error handling with specific exception types and informative error messages.
*   **Documentation**: Update `README.md` files (and create one for new demos) to reflect changes in functionality, setup, or scenarios. Ensure the "How it Works" and "Scenarios to Try" sections are clear and precise.
*   **Dependencies**: Manage all Python dependencies via `pyproject.toml` and ensure `uv.lock` is updated after any changes (`uv sync`).
*   **Testing**: For any new features or significant modifications, include unit tests to verify correctness and robustness.

## Future Work

This repository provides a solid foundation for demonstrating ADK security patterns. Future enhancements could include:

*   **More Advanced ABAC Policies**: Implement more granular policies, including time-based or resource-based access controls.
*   **Dynamic Model Armor Templates**: Explore dynamic selection of Model Armor templates based on user context or agent persona.
*   **Multi-Agent OAuth Flows**: Extend the OAuth demo to a multi-agent scenario where different agents require different scopes or interact with various protected services.
*   **Custom Safety Features**: Develop and integrate additional custom safety and guardrail mechanisms, potentially using smaller, specialized LLMs as classifiers.
*   **Integration with ADK Evaluation**: Create `.evalset.json` files for each demo to enable automated testing and evaluation of their security behaviors using `adk eval`.
*   **Deployment to Vertex AI Agent Engine**: Provide instructions or scripts for deploying these secure agents to a managed service like Vertex AI Agent Engine for production-grade scaling and observability.

