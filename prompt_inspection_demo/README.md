# Prompt Inspection Demo: Client-Side Content Filtering for ADK Agents

## ARTIFACT NAME & RELEVANT LINKS
- **Artifact Name**: ADK Client-Side Prompt Inspection Demo
- **Relevant Files**:
    - `prompt_inspection_demo/agent.py`: The main agent definition, integrating the prompt inspection callback.
- **GitHub Repository**: [Link to this repository's root, if applicable]

## AUTHORSHIP
Sole author and implementer of this Prompt Inspection demonstration.

## CONTEXT
This demo explores basic client-side content filtering as a foundational concept in AI safety. While not as sophisticated as cloud-based services like Model Armor, it demonstrates a quick and direct method to prevent certain inputs from reaching an LLM, often useful for immediate, application-specific guardrails.

**Problem Addressed**: How to implement a lightweight, local mechanism to inspect user prompts for forbidden keywords and block them *before* any LLM processing. This provides an initial layer of defense against unwanted inputs.

**ADK Implementation**:
- The `supervisor_agent` in `prompt_inspection_demo/agent.py` is configured with a `before_model_callback` (`prompt_inspection_callback`).
- This callback directly inspects the incoming prompt's text for a specific, case-insensitive keyword ("sensitive").
- If the keyword is found, the callback returns an `LlmResponse` with a blocked message, effectively short-circuiting the LLM interaction.
- This simple yet effective pattern demonstrates the versatility of ADK callbacks for immediate input validation and content moderation, even without external dependencies.
- The code features clear type hinting and consistent logging, allowing for easy understanding of the filtering logic and its execution flow.

**Relevant "How-to" (from main README)**:
- [Link to Prompt Inspection Demo section in the main README.md for scenarios and execution steps]

## IMPACT & SCOPE
**Impact**:
- **Immediate Input Control**: Provides a rapid method to prevent specific, known problematic inputs from reaching the LLM.
- **Basic Safety Layer**: Serves as a foundational element in a multi-layered safety strategy, complementing more advanced external services.
- **Customizable Filtering**: Demonstrates how application-specific keyword filters can be easily integrated into agent workflows.

**Scope**:
- This demo explicitly showcases a *basic, keyword-based* client-side filtering mechanism using the ADK `before_model_callback`.
- It highlights the direct manipulation of `LlmRequest` and `LlmResponse` objects within a callback to control agent flow.
- The primary purpose is to differentiate simple filtering from more complex semantic understanding, emphasizing the trade-offs and appropriate use cases for each approach.