# ABAC Demo: Attribute-Based Access Control for ADK Agents

## ARTIFACT NAME & RELEVANT LINKS
- **Artifact Name**: ADK Attribute-Based Access Control (ABAC) Demo
- **Relevant Files**:
    - `abac_demo/agent.py`: The main agent definition, integrating ABAC logic.
    - `abac_demo/tools/datastore.py`: The custom tool responsible for enforcing access policies.
    - `abac_demo/data/marketing_data.json`: Sample marketing data (full and limited versions).
    - `abac_demo/data/sales_data.json`: Sample sales data (full and limited versions).
- **GitHub Repository**: [Link to this repository's root, if applicable]

## AUTHORSHIP
Sole author and implementer of this ABAC demonstration.

## CONTEXT
This demo addresses the critical need for fine-grained access control in multi-agent systems, particularly when agents handle sensitive or role-specific data. Without robust access control, an agent might inadvertently expose restricted information or perform unauthorized actions.

**Problem Addressed**: How to dynamically restrict an agent's access to resources (e.g., data stores) based on its assigned attributes (e.g., `AGENT_TYPE`, `ACCESS_LEVEL`). This prevents agents from accessing data outside their designated domain or beyond their privilege level.

**ADK Implementation**:
- The core logic resides in `abac_demo/agent.py`, where the `root_agent` is dynamically configured based on environment variables (`AGENT_TYPE`, `ACCESS_LEVEL`). This simulates different agent "personas" with varying access rights.
- A custom `Tool` (`get_datastore_content` in `abac_demo/tools/datastore.py`) is implemented to act as the policy enforcement point. This tool inspects the agent's configured attributes (passed via `tool_context`) and determines whether to serve 'full' or 'limited' data, or deny access entirely.
- This approach demonstrates how ADK's `ToolContext` can be leveraged to inject runtime information and enforce security policies at the tool execution layer, ensuring that LLM-driven actions adhere to predefined access rules.
- The use of `logging` provides clear visibility into access decisions, demonstrating adherence to observability best practices.

**Relevant "How-to" (from main README)**:
- [Link to ABAC Demo section in the main README.md for scenarios and execution steps]

## IMPACT & SCOPE
**Impact**:
- **Enhanced Security**: Prevents unauthorized data access by agents, crucial for compliance and data privacy in enterprise applications.
- **Systematic Policy Enforcement**: Demonstrates a modular and extensible way to enforce complex access policies, reducing the risk of security vulnerabilities.
- **Improved Observability**: Detailed logging allows for auditing and debugging of access control decisions, which is vital for maintaining secure operations.

**Scope**:
- This demo's scope is to clearly demonstrate a foundational ABAC pattern within a simple two-agent (marketing/sales) and two-access-level (employee/manager) setup.
- It showcases the ability to apply dynamic, attribute-driven security logic directly within custom ADK tools.
- The principles demonstrated are directly applicable to more complex scenarios involving multiple agent roles, diverse data sources, and intricate policy rules, serving as a scalable blueprint for securing agentic workflows.