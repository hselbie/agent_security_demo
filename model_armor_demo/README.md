# Model Armor Demo: Content Safety for ADK Agents

## ARTIFACT NAME & RELEVANT LINKS
- **Artifact Name**: ADK Google Cloud Model Armor Integration Demo
- **Relevant Files**:
    - `model_armor_demo/agent.py`: The main agent definition, integrating the Model Armor callback.
    - `model_armor_demo/setup_model_armor.py`: One-time script to configure the Model Armor template.
- **GitHub Repository**: [Link to this repository's root, if applicable]

## AUTHORSHIP
Sole author and implementer of this Model Armor demonstration.

## CONTEXT
This demo addresses the paramount concern of content safety in AI applications. Without proactive filtering, agents powered by Large Language Models (LLMs) risk generating harmful, biased, or inappropriate content, leading to significant ethical and reputational issues. Google Cloud Model Armor provides a robust, pre-trained service for detecting such content.

**Problem Addressed**: How to intercept and sanitize user prompts for sensitive or harmful information *before* they are processed by the LLM, ensuring safe and responsible AI interactions. This prevents the LLM from being exposed to and potentially propagating unsafe content.

**ADK Implementation**:
- The `supervisor_agent` in `model_armor_demo/agent.py` uses a `before_model_callback` (`model_armor_callback`) to intercept all incoming prompts.
- This callback makes an asynchronous call to the Google Cloud Model Armor API, evaluating the prompt against a configured safety template (`ma-all-low`).
- If Model Armor flags the content (e.g., as PII, hate speech, dangerous), the callback programmatically prevents the LLM from executing and returns a predefined safety response.
- This demonstrates a crucial application of ADK's callback mechanism for implementing external safety guardrails, showcasing a defense-in-depth approach to AI safety.
- The code includes robust error handling for API interactions and comprehensive logging for all safety decisions, adhering to L5 observability standards.

**Relevant "How-to" (from main README)**:
- [Link to Model Armor Demo section in the main README.md for scenarios and execution steps]

## IMPACT & SCOPE
**Impact**:
- **Ensures Responsible AI**: Prevents the generation and propagation of harmful, biased, or sensitive content, upholding ethical AI principles.
- **Reduces Risk**: Mitigates legal, reputational, and compliance risks associated with unsafe AI outputs.
- **Scalable Safety**: Demonstrates integration with a managed, scalable cloud service for AI safety, suitable for enterprise-grade applications.

**Scope**:
- This demo focuses on implementing a *pre-LLM* content safety filter using Model Armor, effectively acting as an input guardrail.
- It showcases the ADK `before_model_callback` pattern for integrating external, specialized services into the agent's processing pipeline.
- The `setup_model_armor.py` script further demonstrates managing external service configurations required for robust AI systems.
- The principles are generalizable to other pre-processing or post-processing steps requiring external API interactions for safety, compliance, or data enrichment.