# Autonomous Agentic PR Reviewer (CI/CD)

An asynchronous, multi-agent code review engine built with **LangGraph**, **FastAPI**, and **Pydantic**. It scans incoming Pull Requests for security vulnerabilities and architectural anti-patterns in parallel, enforcing deterministic schemas to prevent hallucinated reviews.

---

## 🏗️ System Architecture

Rather than relying on monolithic LLM prompts that suffer from context loss and high latency, this system splits inspection responsibilities across specialized agents executing concurrently via LangGraph.

```mermaid
flowchart TD
    Start([PR Diff Trigger]) --> SecurityAgent[🛡️ Security Specialist Agent]
    Start --> ArchAgent[🏗️ Architecture Specialist Agent]
    
    SecurityAgent -->|Security Findings| Synthesizer[🧠 Synthesizer & Arbiter]
    ArchAgent -->|Structural Findings| Synthesizer
    
    Synthesizer --> Decision{Critical Flaws Found?}
    Decision -->|Yes| Reject[❌ REJECT PR + Actionable Fixes]
    Decision -->|No| Approve[✅ APPROVE PR]