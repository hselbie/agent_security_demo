# OAuth 2.0 Demo: Delegated Authorization for ADK Agents

## ARTIFACT NAME & RELEVANT LINKS
- **Artifact Name**: ADK OAuth 2.0 Delegated Authorization Demo
- **Relevant Files**:
    - `oauth_demo/agent.py`: The main BigQuery agent definition, integrating OAuth.
    - `oauth_demo/a2a_server.py`: The A2A server demonstrating OAuth flow handling.
    - `oauth_demo/agent_executor.py`: Custom executor for managing ADK agent execution and OAuth callbacks.
- **GitHub Repository**: [Link to this repository's root, if applicable]

## AUTHORSHIP
Sole author and implementer of this OAuth 2.0 demonstration.

## CONTEXT
This demo addresses the critical requirement for AI agents to securely interact with user-specific data and services in a delegated manner. In enterprise environments, agents often need to access cloud resources (like databases, calendars, or documents) on behalf of an authenticated user, without handling their credentials directly. OAuth 2.0 is the industry-standard protocol for achieving this.

**Problem Addressed**: How to enable an ADK agent to access a protected Google Cloud service (BigQuery, in this case) using a user's delegated authorization, involving an interactive consent flow, secure token management, and session-based caching of credentials.

**ADK Implementation**:
- The `BigQueryToolset` in `oauth_demo/agent.py` is configured with `BigQueryCredentialsConfig`, which leverages OAuth 2.0 parameters defined in the centralized `.env` file.
- When the agent attempts to use a BigQuery tool for the first time, the ADK framework automatically triggers an OAuth consent flow. This involves redirecting the user to a Google authorization URL.
- The custom `ADKAgentExecutor` in `oauth_demo/agent_executor.py` and the `A2ARESTFastAPIApplication` in `oauth_demo/a2a_server.py` are specifically designed to handle the OAuth callback, exchange the authorization code for an access token, and manage the credential securely within the agent's session state.
- This demonstrates a sophisticated interaction between the ADK runtime, custom executors, and external OAuth providers, showcasing secure credential management and delegated authority.
- All components are enhanced with extensive type hinting and structured logging, providing deep insights into the OAuth handshake and agent operations.

**Relevant "How-to" (from main README)**:
- [Link to OAuth Demo section in the main README.md for scenarios and execution steps]

## IMPACT & SCOPE
**Impact**:
- **Secure Delegated Access**: Enables agents to safely interact with user-specific protected resources without ever seeing or storing user credentials.
- **Enhanced User Trust**: Provides a transparent and auditable consent process, increasing user confidence in agent capabilities.
- **Enterprise Integration**: Crucial for building agents that integrate with a wide array of enterprise applications requiring user-specific authorization (e.g., CRM, HR systems, project management tools).

**Scope**:
- This demo covers the full lifecycle of an interactive OAuth 2.0 authorization code flow within an ADK agent, from initiation to token management.
- It specifically demonstrates integration with Google BigQuery, but the underlying ADK and A2A patterns are applicable to any service supporting OAuth 2.0.
- The custom `AgentExecutor` highlights how to extend ADK's core capabilities to handle complex asynchronous flows like external authentication. This is a complex example and an L5 understanding of the execution model.