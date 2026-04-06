import json
from models import Action, Observation, Reward

class ResolveEnv:
    def __init__(self):
        # Load the mock DB
        with open('data.json', 'r') as f:
            self.db = json.load(f)
        
        self.current_ticket = None
        self.agent_state = self._get_blank_state()
        
    def _get_blank_state(self):
        return {
            "has_checked_user": False,
            "has_checked_policy": False,
            "is_resolved": False,
            "ticket_text": "",
            "last_api_response": "Awaiting initial action."
        }

    def reset(self, ticket_id="t2"):
        """Loads a specific ticket and wipes history."""
        self.agent_state = self._get_blank_state()
        
        # Find the ticket
        ticket = next((t for t in self.db['tickets'] if t['id'] == ticket_id), None)
        self.current_ticket = ticket
        self.agent_state["ticket_text"] = ticket["text"]
        
        return Observation(
            ticket_text=self.agent_state["ticket_text"],
            last_api_response="System initialized. Available tools: search_user, check_order, check_policy, issue_refund, escalate, reply",
            is_resolved=False
        )

    def state(self):
        """Returns the current state."""
        return Observation(
            ticket_text=self.agent_state["ticket_text"],
            last_api_response=self.agent_state["last_api_response"],
            is_resolved=self.agent_state["is_resolved"]
        )

    def step(self, action: Action):
        """The router and reward shaping engine."""
        tool = action.tool_name
        args = action.tool_arguments
        
        reward = 0.0
        response = ""
        done = False

        try:
            # Parse arguments safely
            args_dict = json.loads(args) if args else {}

            # --- TOOL ROUTER & REWARD SHAPING ---
            
            if tool == "search_user":
                email = args_dict.get("email", "")
                user = next((u for u in self.db["users"].values() if u["email"] == email), None)
                if user:
                    response = f"Found user: {user['name']}"
                    if not self.agent_state["has_checked_user"]:
                        reward = 0.1  # Reward: +0.1 for successful lookup
                        self.agent_state["has_checked_user"] = True
                else:
                    response = "User not found."
                    reward = -0.1

            elif tool == "check_policy":
                response = f"Refund Policy: {self.db['policy']['rule']}"
                if not self.agent_state["has_checked_policy"]:
                    reward = 0.2  # Reward: +0.2 for checking rules
                    self.agent_state["has_checked_policy"] = True
                    
            elif tool == "check_order":
                order_id = args_dict.get("order_id", "")
                order = self.db["orders"].get(order_id)
                if order:
                    response = f"Order status: {order['status']}, Days since purchase: {order['days_since_purchase']}, Item: {order['item']}"
                else:
                    response = "Order not found."
                    
            elif tool == "issue_refund":
                if not self.agent_state["has_checked_policy"]:
                    response = "ACTION BLOCKED: Policy violation. Cannot issue refund without checking policy first."
                    reward = -0.5  # Penalty: -0.5 for blind refund
                else:
                    response = "Refund issued successfully."
                    done = True
                    self.agent_state["is_resolved"] = True
                    reward = 1.0 # Final task success
                    
            elif tool == "escalate":
                response = "Ticket escalated to human support."
                done = True
                self.agent_state["is_resolved"] = True
                reward = 1.0 # Final task success

            elif tool == "reply":
                response = f"Message sent to customer: {args_dict.get('message')}"
                done = True
                self.agent_state["is_resolved"] = True
                reward = 1.0 # Final task success

            else:
                response = f"Unknown tool: {tool}"
                reward = -0.1

        except Exception as e:
            response = f"System Error processing action: {str(e)}"
            reward = -0.2

        self.agent_state["last_api_response"] = response

        obs = Observation(
            ticket_text=self.agent_state["ticket_text"],
            last_api_response=response,
            is_resolved=done
        )
        
        return obs, Reward(step_reward=reward), done, {"info": "step complete"}
    
    def grade(self):
        """Deterministic graders for the 3 tasks."""
        if not self.current_ticket:
            return 0.0

        ticket_id = self.current_ticket["id"]
        
        # Easy Task: Did they reply?
        if ticket_id == "t1":
            if self.agent_state["is_resolved"] and "Message sent" in self.agent_state["last_api_response"]:
                return 1.0
            return 0.0
            
        # Medium Task: Did they successfully issue a refund?
        elif ticket_id == "t2":
            if self.agent_state["is_resolved"] and "Refund issued successfully" in self.agent_state["last_api_response"]:
                return 1.0
            return 0.0
            
        # Hard Task: Did they escalate (and avoid the trap of refunding)?
        elif ticket_id == "t3":
            if self.agent_state["is_resolved"]:
                if "escalated" in self.agent_state["last_api_response"].lower():
                    return 1.0
                elif "Refund issued" in self.agent_state["last_api_response"]:
                    return 0.0 # Failed the trap!
            return 0.0
            
        return 0.0