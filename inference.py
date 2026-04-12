import os
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

from models import ResolveAction
from server.resolve_environment import ResolveEnvironment

load_dotenv()

# ================= ENV CONFIG ================= #
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")

MAX_STEPS = 8


# ================= LOGGING ================= #
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step, action, reward, done, error=None):
    err = error if error else "null"
    done_str = str(done).lower()
    action_str = json.dumps(action).replace(" ", "")
    print(
        f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_str} error={err}",
        flush=True,
    )


def log_end(success, steps, score, rewards):
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ================= SAFE MODEL CALL ================= #
async def get_action(client, messages):
    try:
        completion = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content.strip()
        return json.loads(content)

    except Exception:
        # fallback safe action
        return {
            "tool_name": "escalate",
            "tool_arguments": "{}"
        }


# ================= TASK RUNNER ================= #
async def run_task(client, task_id, task_name):
    env = ResolveEnvironment()

    rewards = []
    steps_taken = 0
    success = False
    final_score = 0.0

    log_start(task_name, "ResolveEnv", MODEL_NAME)

    try:
        env.load_specific_ticket(task_id)

        history = [
            {
                "role": "system",
                "content": """You are a customer support agent.
Return ONLY JSON:
{"tool_name": "...", "tool_arguments": "..."}"""
            }
        ]

        for step in range(1, MAX_STEPS + 1):
            steps_taken = step

            user_input = f"""
Ticket: {env.agent_state["ticket_text"]}
Last response: {env.agent_state["last_api_response"]}
What is next action?
"""

            history.append({"role": "user", "content": user_input})

            action_dict = await get_action(client, history)

            try:
                action = ResolveAction(**action_dict)
            except Exception:
                action = ResolveAction(
                    tool_name="escalate",
                    tool_arguments="{}"
                )

            obs = env.step(action)

            reward = obs.reward
            done = obs.done

            rewards.append(reward)

            log_step(step, action_dict, reward, done)

            history.append({"role": "assistant", "content": json.dumps(action_dict)})

            if done:
                break

        final_score = float(env.grade())
        final_score = max(0.0, min(final_score, 1.0))
        success = final_score >= 0.7

    except Exception as e:
        log_step(steps_taken, {"error": "crash"}, -1.0, True, str(e))

    finally:
        log_end(success, steps_taken, final_score, rewards)


# ================= MAIN ================= #
async def main():
    client = AsyncOpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
    )

    tasks = [
        ("t1", "easy"),
        ("t2", "medium"),
        ("t3", "hard"),
    ]

    for t_id, t_name in tasks:
        await run_task(client, t_id, t_name)


if __name__ == "__main__":
    asyncio.run(main())
