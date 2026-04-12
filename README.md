# ResolveEnv — Customer Support Decision-Making Benchmark

ResolveEnv is a real-world OpenEnv environment that simulates **customer support ticket resolution workflows**, requiring agents to reason over user data, order history, and business policies using structured tools.

This environment evaluates **multi-step reasoning, tool usage, and policy compliance** — core capabilities required in production AI agents.

---

## 🚀 Why This Environment Matters

Most benchmarks test:
- text generation
- simple Q&A

ResolveEnv tests:
- **decision-making under constraints**
- **multi-step tool usage**
- **policy-aware reasoning**
- **error prevention (critical in real systems)**

👉 This reflects real-world enterprise workflows (customer support, operations, CRM systems).

---

## 🧠 Environment Overview

The agent acts as a **Level-1 Customer Support AI** and must:

1. Understand a customer ticket
2. Extract relevant identifiers (email, order_id)
3. Use internal tools to investigate
4. Apply business rules correctly
5. Resolve or escalate the issue

---

## 🧰 Available Tools (Action Space)

The agent must output structured actions:

```json
{
  "tool_name": "check_order",
  "tool_arguments": "{\"order_id\": \"ord_001\"}"
}

| Tool           | Description               |
| -------------- | ------------------------- |
| `search_user`  | Lookup user by email      |
| `check_order`  | Retrieve order details    |
| `check_policy` | Get refund rules          |
| `issue_refund` | Process refund (if valid) |
| `escalate`     | Escalate to human         |
| `reply`        | Respond to customer       |



| Behavior           | Score |
| ------------------ | ----- |
| Checked user       | +0.2  |
| Checked order      | +0.2  |
| Checked policy     | +0.3  |
| Correct resolution | +0.3  |



resolve-env/
├── server/
│   ├── app.py
│   ├── resolve_environment.py
├── models.py
├── inference.py
├── openenv.yaml
├── data.json
├── Dockerfile
├── README.md

---

## 🛠️ Setup & Usage Instructions

### Docker (Recommended for Hugging Face Space)
Build and run the environment in a Docker container:
```bash
docker build -t openenv .
docker run -p 7860:7860 openenv
```
The server will start at `http://localhost:7860`.

### Local Execution
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Set API keys in `.env` (`HF_TOKEN` or `GEMINI_API_KEY`, etc.).
3. Run the inference baseline:
```bash
python inference.py
```

---

## 📊 Baseline Scores

We evaluated the baseline agent (Gemini 2.5 Flash) across the three defined tasks. Tests demonstrate clear progression across difficulties:

| Task ID | Task Name                | Difficulty | Avg Score | Success | Steps |
| ------- | ------------------------ | ---------- | --------- | ------- | ----- |
| t1      | Check Order Status       | Easy       | 1.0       | Yes     | 2     |
| t2      | Standard Refund          | Medium     | 1.0       | Yes     | 4     |
| t3      | Policy Trap Escalation   | Hard       | 1.0       | Yes     | 4     |

*(Note: Without API keys running inference.py locally defaults to score=0.01 with auth errors.)*
