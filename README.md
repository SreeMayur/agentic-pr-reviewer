# Autonomous Agentic PR Reviewer (CI/CD)

An asynchronous, multi-agent code review engine built with **LangGraph**, **FastAPI**, and **Pydantic**. It scans incoming Pull Requests for security vulnerabilities and architectural anti-patterns in parallel, enforcing deterministic schemas to prevent hallucinated reviews.

---

## 🏗️ System Architecture & Engineering 

This project goes beyond a standard LLM wrapper by implementing an event-driven, multi-agent architecture designed for enterprise CI/CD workflows. 

It is built to be strictly asynchronous and secure, ensuring it can handle high-frequency webhook traffic without blocking the main event loop.

### Core Workflow
1. **Event Reception (FastAPI):** Listens for `pull_request` events via GitHub Webhooks.
2. **Cryptographic Verification:** Validates incoming payloads using HMAC-SHA256 signatures against a secure webhook secret to prevent spoofing.
3. **Background Delegation:** Immediately returns a `202 Accepted` or `200 OK` to GitHub to prevent timeouts, while offloading the LLM inference to a FastAPI `BackgroundWorker`.
4. **Agentic Orchestration (LangGraph):** 
   - Utilizes a **fan-out / fan-in** architecture.
   - **Fan-out:** The PR diff is parsed and sent simultaneously to specialized agents (e.g., Security Scanner, Architecture Reviewer).
   - **Fan-in:** A synthesis node aggregates the parallel outputs, resolving conflicting advice and formatting a final verdict.
5. **Asynchronous Feedback (httpx):** Calls the GitHub REST API asynchronously to post the formatted markdown review directly to the PR conversation timeline.

### Tech Stack & Design Decisions
- **Framework:** FastAPI for high-performance, async webhook handling.
- **Orchestration:** LangGraph for stateful, multi-agent routing.
- **LLM:** Google Gemini Flash for low-latency, highly structured outputs.
- **Security:** Strict `.env` management (PAT, Webhook Secrets, API Keys) and HMAC payload validation.
- **Network:** Asynchronous HTTP clients (`httpx`) to ensure the server remains non-blocking during external API calls.

### Business Value
By automating the initial pass of code reviews, this pipeline eliminates human bottlenecks for standard security and architectural anti-patterns, reducing the time-to-merge and protecting the main branch from hardcoded credentials or state-management flaws.

## 🚀 Quick Start / Local Setup

### Prerequisites
- Python 3.10+
- [ngrok](https://ngrok.com/) for local tunneling
- A GitHub Personal Access Token (PAT) with `repo` scope

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/agentic-pr-reviewer.git](https://github.com/yourusername/agentic-pr-reviewer.git)
   cd agentic-pr-reviewer
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
Create a `.env` file in the root directory and add the following:
```env
GOOGLE_API_KEY=your_gemini_api_key
GITHUB_WEBHOOK_SECRET=your_custom_secret
GITHUB_TOKEN=your_github_pat
```

### Running the Engine

1. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --reload
   ```

2. **Start the ngrok tunnel (in a separate terminal):**
   ```bash
   ngrok http 8000
   ```

3. **Configure GitHub:**
   Go to your repository settings -> Webhooks. Add your ngrok URL (`https://<your-ngrok-url>/webhook`), set the Content type to `application/json`, and paste your webhook secret.

*Maintained by the core development team.*
