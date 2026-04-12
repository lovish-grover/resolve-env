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