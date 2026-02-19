This repo contains example agents that are built from popular Agent SDKs.

Those agents can work with the [kube agentic gateway](https://github.com/kubernetes-sigs/kube-agentic-networking).


Disclaimer: The information below is provided "as is" for informational purposes only. Agent capabilities, integrations, and best practices change rapidly and may become outdated.

## Comparison of Popular AI/ML Agent SDKs

### 1. OpenAI Agents SDK

The OpenAI Agents SDK is a lightweight, Python-first framework designed to build agentic workflows and multi-agent systems using minimal primitives (agents, handoffs, guardrails). It includes built-in tracing for debugging and supports function tools.

**Strengths:**

Low Abstraction: 

Very few new concepts to learn, agents are treated as standard Python objects. The barrier is lower for building agentic systems.

Native Handoffs: 

Built-in ["Handoff"](https://openai.github.io/openai-agents-python/handoffs/) primitives allow one agent to transfer control to another seamlessly.

**Limitations:**

Limited Orchestration: 

Compared to frameworks like LangChain or LangGraph, low-level control over agent flow can be limited. Developers often treats the agent as a "black box" where you provide a prompt and hope for the best. The agent might "hallucinate" a loop or skip a step.

Vendor bundle lock-in: 

While model-agnostic via LiteLLM, advanced features such as mutlti-provider workflows still require set up and some features may only work with OpenAI.

### 2. Anthropic SDK

Anthropic’s agent framework focuses on safety-oriented, long-context reasoning and structured workflows, often with a defensive architecture designed for secure applications. Its SDK supports robust permissioning and safety layers.

**Strengths:**

Token Efficiency: 

MCP reduces "context bloat" by providing standardized tool definitions that don't need to be re-sent in every prompt. It is built for large contexts (e.g., 100k+ tokens), useful for document-heavy tasks.

Superior Tool Use: Claude-3.5 and 4.0 are natively trained on MCP, resulting in the lowest "hallucination rate" for API calls.

Safety-first design: Security model and permissioning mechanisms help mitigate agent risks.

**Limitations:**

No Native Orchestrator: Anthropic SDK provides the "tools" but not the Orchestrator for multi-agent loops. Developers usually pair this with LangGraph.

Tighter ecosystem: Best when used with Anthropic models. Portability requires adaptors or compatibility layers.

### 3. LangChain (LangGraph)
LangChain is a general-purpose LLM application framework (often used with LangGraph) aiming to compose chains of LLM calls, tool integrations, workflows, and multi-step reasoning.

**Strengths:**

Mature ecosystem: Many integrations (databases, search, APIs), templates, and community tooling.

Graph structure:

LangGraph is the "gold standard" for low-level control. Developers actually draw a map (graph) of your code and 100% control over the loop. For example, the agent cannot exit the loop unless you define an edge that leads to the END node.

Model agnostic: Works with many LLM providers via configs and extensions.

Persistence: Automatically saves the agent's state to a database so a user can resume a conversation days later.

**Limitations:**

Learning Curve: Requires learning graph theory concepts (Nodes, Edges, State).

Performance: The heavy abstraction can add 50-100ms of latency per turn.

### 4. Pydantic AI SDK

Pydantic AI is a model-agnostic SDK built on Pydantic that simplifies structured outputs, validation, and developer ergonomics.

**Strengths:**

Model agnostic: Works across many providers (OpenAI, Anthropic, Gemini, etc.).

Type Safety: Uses Python type hints to ensure an LLM's output matches exactly what your database expects.

Simple API: Easy to prototype structured agent workflows.

Deterministic Logic: The SDK recently moved way from purely "autonomous" reasoning to a more controlled, software-engineered flow through (pydantic graph)[https://ai.pydantic.dev/api/pydantic_graph/graph/]

**Limitations:**

Limited built-in integrations: Fewer "out-of-the-box" connectors for tools like Salesforce or Jira compared to LangChain. 

### 5. AWS Bedrock SDK (AgentCore)

Bedrock is AWS’s managed platform for generative AI, and its AgentCore SDK uses foundational components to build agent workloads. It combines LLMs with enterprise compliance, observability, and tools like memory and Gateway service.

**Strengths:**

IAM Security: Native integration with AWS Identity and Access Management, so there in no API keys to leak.

Enterprise readiness: Built-in compliance, security, and governance capabilities.

Observability & tooling: Logging and monitoring facilitate enterprise pipelines.

**Limitations:**

Infrastructure Heavy: Setting up an agent requires managing Lambdas, S3 buckets, and IAM roles.

Tied to AWS ecosystem: Best performance and integration when used on AWS. It is less portable to other clouds.

### 6. Google SDK (ADK)

Google’s Agent Development Kit sits within the Google GenAI/Vertex AI ecosystem. It attempts to offer tooling for multi-agent workflows and deeper integration with Google Cloud services.

**Strengths:**

Agent2Agent (A2A): A sophisticated protocol for hierarchical agents (Manager -> Worker).

Workflow Agents: These act as controllers that manage sub-agents in specific patterns such as SequentialAgent, ParallelAgent and LoopAgent.

**Limitations:**

Evolving ecosystem: community adoption and documentation are still smaller than more mature SDKs.

### 7. LiteLLM SDK
LiteLLM is the industry standard for avoiding vendor lock-in.

**Strengths:**

Standardization: Maps any model (OpenAI, Anthropic, Ollama) to a single OpenAI-compatible format.

Cost & Budgeting: Built-in tracking to kill an agent’s API access if it exceeds a set budget (e.g., $\$10.00$/day).

**Limitations:**

No Orchestration: It doesn't understand "intent" or "state." It is a proxy, not an orchestrator.

Setup complexity: Self-hosting, database, and Redis configuration can be non-trivial.

Not tailored to agent loops: Needs integration with a higher-level agent framework (e.g., OpenAI Agents SDK, ADK, LangChain).