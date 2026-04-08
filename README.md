# 🚀 ResolveEnv: Agentic Customer Support Benchmark

![Phase 1](https://img.shields.io/badge/Phase_1-PASSED-brightgreen?style=for-the-badge) ![Phase 2](https://img.shields.io/badge/Phase_2-PASSED-brightgreen?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge) ![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-orange?style=for-the-badge)

**ResolveEnv** is a rigorously engineered, multi-step environment built for the **Meta PyTorch Hackathon x Scaler School of Technology**. Designed using the `openenv-core` framework, it evaluates the ability of Large Language Models (LLMs) to act as Level 1 Customer Support Agents. 

The benchmark tests an agent's ability to utilize external tools, maintain conversational state, and strictly adhere to corporate policies (such as a 30-day refund window) without hallucinating.

---

## 🎯 The Challenge: 3-Tier Evaluation

The environment forces the agent to interact with a simulated database and policy engine through strict, JSON-formatted actions. It evaluates agents across three progressively difficult tasks:

1. **Task 1: Check Order Status (Easy)**
   * **Goal:** Extract user details, query the database, and inform the user of a delayed shipment.
   * **Required Tools:** `check_order`, `reply`
2. **Task 2: Standard Refund (Medium)**
   * **Goal:** Process a standard return within the allowed timeframe.
   * **Required Tools:** `check_order`, `check_policy`, `issue_refund`, `reply`
3. **Task 3: Policy Trap (Hard)**
   * **Goal:** Recognize a customer attempting to bypass the 30-day return policy and successfully escalate the ticket rather than issuing an unauthorized refund.
   * **Required Tools:** `check_order`, `check_policy`, `escalate`

---

## 🏗️ Architecture & Tech Stack

This project is built for high reliability and seamless deployment across automated grading servers (like Hugging Face Spaces).

* **Framework:** `openenv-core`, FastAPI, Uvicorn
* **Agent Integration:** Standardized `openai` SDK proxy routing (Compatible with Gemini, Llama, and GPT models).
* **Data Validation:** Strict `pydantic` schemas for Action and Observation spaces to prevent catastrophic LLM hallucinations.
* **Containerization:** Dockerized for reproducible environments.

### 🛡️ Enterprise-Grade Deployment Features
* **AWS ECR Base Image:** Bypasses standard Docker Hub rate limits by utilizing the `public.ecr.aws/docker/library/python:3.10-slim` mirror, ensuring 100% build success during high-traffic hackathon evaluations.
* **Native Python Healthchecks:** Replaces standard `curl` dependencies with native `urllib` polling for robust container lifecycle management.
* **Strict Open Interval Scoring:** Reward shaping is strictly clamped to `[0.01, 0.99]` to comply with strict `< 1.0` mathematical validator bounds.

---

## 📂 Project Structure

```text
resolve-env/
├── server/
│   ├── app.py                  # FastAPI server and OpenEnv HTTP wrapper
│   └── resolve_environment.py  # Core logic, state management, and tool execution
├── models.py                   # Pydantic schemas for ResolveAction and ResolveObservation
├── inference.py                # The AI agent logic and evaluation loop
├── openenv.yaml                # Mandatory task definitions for the OpenEnv validator
├── pyproject.toml              # Modern Python packaging and server entry points
├── Dockerfile                  # Production-ready container definition (Port 7860)
└── README.md

pip install uv
uv sync

API_BASE_URL="[https://generativelanguage.googleapis.com/v1beta/openai/](https://generativelanguage.googleapis.com/v1beta/openai/)"
MODEL_NAME="gemini-1.5-flash"
API_KEY="your_api_key_here"

python inference.py ```


