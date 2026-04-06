import os
import json
import asyncio
from google import genai
from google.genai import types
from models import ResolveAction, ResolveObservation
from server.resolve_environment import ResolveEnvironment
from dotenv import load_dotenv

load_dotenv() 

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error=None):
    err_str = f" error={error}" if error else ""
    print(f"[STEP] step={step} action={json.dumps(action)} reward={reward:.2f} done={done}{err_str}", flush=True)

def log_end(success, steps, score, rewards):
    print(f"[END] success={success} steps={steps} score={score:.2f} rewards={rewards}", flush=True)

SYSTEM_PROMPT = """You are a Level 1 Customer Support AI. 
Your goal is to investigate and resolve the user's ticket IMMEDIATELY by using the provided tools.
Extract the email or order_id from the customer's message to use in your tools.
Do NOT ask the customer for more information. 

CRITICAL BUSINESS RULES:
1. You MUST check the order status using `check_order` before taking action.
2. If the customer requests a refund, you MUST check the refund policy using `check_policy` BEFORE attempting to use `issue_refund`. 
3. If the customer is only asking for a status update (e.g., where is my order), use the `reply` tool to tell them the current status.

You MUST output your action strictly as a JSON object matching the requested schema.
Available tools: search_user, check_order, check_policy, issue_refund, escalate, reply"""

async def run_task(client, env: ResolveEnvironment, task_id, task_name, max_steps=10):
    log_start(task=task_name, env="ResolveEnv", model=MODEL_NAME)
    
    # Load specific ticket
    env.load_specific_ticket(ticket_id=task_id)
    
    # Manually create the observation
    obs = ResolveObservation(
        ticket_text=env.agent_state["ticket_text"],
        last_api_response="System initialized. Available tools: search_user, check_order, check_policy, issue_refund, escalate, reply",
        is_resolved=False,
        done=False,
        reward=0.0
    )
    
    rewards = []
    steps_taken = 0
    history = []
    
    action_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "tool_name": types.Schema(
                type=types.Type.STRING, 
                description="The name of the tool to use (e.g., 'search_user', 'check_order', 'check_policy', 'issue_refund', 'escalate', 'reply')"
            ),
            "tool_arguments": types.Schema(
                type=types.Type.STRING, 
                description="JSON formatted string of arguments for the tool. Use '{}' if none."
            )
        },
        required=["tool_name", "tool_arguments"]
    )
    
    for step in range(1, max_steps + 1):
        steps_taken = step
        user_msg = f"Customer Ticket: {env.agent_state['ticket_text']}\nLast API Response: {env.agent_state['last_api_response']}\nWhat is your next action?"
        history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_msg)]))
        
        try:
            print("  (Pausing for 12s to respect API rate limits...)", flush=True)
            await asyncio.sleep(12) 
            
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=action_schema,
                    temperature=0.0
                )
            )
            
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            action_dict = json.loads(raw_text)
            action_obj = ResolveAction(**action_dict)
            
            history.append(types.Content(role="model", parts=[types.Part.from_text(text=response.text)]))
            
            obs = env.step(action_obj)
            rewards.append(obs.reward)
            
            log_step(step=step, action=action_dict, reward=obs.reward, done=obs.done)
            if obs.done: break
                
        except Exception as e:
            log_step(step=step, action={"error": "failed"}, reward=-1.0, done=True, error=str(e))
            break

    final_score = env.grade()
    log_end(success=final_score >= 1.0, steps=steps_taken, score=final_score, rewards=rewards)

async def main():
    env = ResolveEnvironment()
    client = genai.Client(api_key=API_KEY)
    
    tasks = [
        ("t1", "Check_Order_Status_Easy"), 
        ("t2", "Standard_Refund_Medium"), 
        ("t3", "Policy_Trap_Escalation_Hard")
    ]
    
    for t_id, t_name in tasks:
        await run_task(client, env, task_id=t_id, task_name=t_name)

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())