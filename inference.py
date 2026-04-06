import os
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

from models import ResolveAction, ResolveObservation
from server.resolve_environment import ResolveEnvironment

load_dotenv() 

# 1. MANDATORY VARIABLES (Matching Hackathon Rules exactly)
API_BASE_URL = os.getenv("API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")
# Safely fall back through the token names
API_KEY = os.getenv("HF_TOKEN", os.getenv("OPENAI_API_KEY", os.getenv("GEMINI_API_KEY", "")))

# 2. STRICT STDOUT LOGGING (Lowercase booleans, exact spacing)
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error=None):
    err_str = error if error else "null"
    done_str = str(done).lower() # Rule: lowercase booleans
    action_str = json.dumps(action).replace(" ", "") # Compact JSON string
    print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_str} error={err_str}", flush=True)

def log_end(success, steps, score, rewards):
    success_str = str(success).lower() # Rule: lowercase booleans
    rewards_str = ",".join([f"{r:.2f}" for r in rewards]) # Rule: 0.00,0.00,1.00 formatting
    print(f"[END] success={success_str} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

SYSTEM_PROMPT = """You are a Level 1 Customer Support AI. 
Your goal is to investigate and resolve the user's ticket IMMEDIATELY by using the provided tools.
Extract the email or order_id from the customer's message to use in your tools.
Do NOT ask the customer for more information. 

CRITICAL BUSINESS RULES:
1. You MUST check the order status using `check_order` before taking action.
2. If the customer requests a refund, you MUST check the refund policy using `check_policy` BEFORE attempting to use `issue_refund`. 
3. If the customer is only asking for a status update, use the `reply` tool to tell them the current status.

You MUST output your action STRICTLY as a valid JSON object with EXACTLY two keys:
- "tool_name": (string) The tool to use.
- "tool_arguments": (string) A JSON-formatted string of the arguments. Use "{}" if none.

Available tools: search_user, check_order, check_policy, issue_refund, escalate, reply"""

async def run_task(client, env: ResolveEnvironment, task_id, task_name, max_steps=10):
    log_start(task=task_name, env="ResolveEnv", model=MODEL_NAME)
    
    env.load_specific_ticket(ticket_id=task_id)
    obs = ResolveObservation(
        ticket_text=env.agent_state["ticket_text"],
        last_api_response="System initialized. Available tools: search_user, check_order, check_policy, issue_refund, escalate, reply",
        is_resolved=False,
        done=False,
        reward=0.0
    )
    
    rewards = []
    steps_taken = 0
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for step in range(1, max_steps + 1):
        steps_taken = step
        user_msg = f"Customer Ticket: {env.agent_state['ticket_text']}\nLast API Response: {env.agent_state['last_api_response']}\nWhat is your next action? Return ONLY valid JSON."
        history.append({"role": "user", "content": user_msg})
        
        try:
            # MANDATORY: Using the OpenAI SDK Client 
            completion = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=history,
                temperature=0.0,
                response_format={"type": "json_object"} # Standard JSON mode to bypass Pydantic errors
            )
            
            raw_text = completion.choices[0].message.content.strip()
            action_dict = json.loads(raw_text)
            
            # Map it back to our strict Pydantic model for the environment
            action_obj = ResolveAction(**action_dict)
            history.append({"role": "assistant", "content": raw_text})
            
            obs = env.step(action_obj)
            rewards.append(obs.reward)
            
            log_step(step=step, action=action_dict, reward=obs.reward, done=obs.done)
            if obs.done: break
                
        except Exception as e:
            log_step(step=step, action={"error": "failed"}, reward=-1.0, done=True, error=str(e))
            break

    final_score = env.grade()
    success = final_score >= 1.0
    log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)

async def main():
    env = ResolveEnvironment()
    
    # 3. Initialize OpenAI Client (Required by Hackathon)
    async with AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY) as client:
        tasks = [
            ("t1", "Check_Order_Status_Easy"), 
            ("t2", "Standard_Refund_Medium"), 
            ("t3", "Policy_Trap_Escalation_Hard")
        ]
        for t_id, t_name in tasks:
            print("  (Pausing for 12s to respect API rate limits...)", flush=True)
            await asyncio.sleep(12) 
            await run_task(client, env, task_id=t_id, task_name=t_name)

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())