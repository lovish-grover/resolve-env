import json
import os
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import ResolveAction, ResolveObservation

class ResolveEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        # Load the mock DB reliably regardless of where it is run
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json')
        if not os.path.exists(db_path):
            db_path = 'data.json'
            
        with open(db_path, 'r') as f:
            self.db = json.load(f)
            
        self._state = State(episode_id=str(uuid4()), step_count=0)
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

    def reset(self) -> ResolveObservation:
        """Resets to a random or default ticket for the session."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.agent_state = self._get_blank_state()
        
        # Defaulting to Task 2 (Medium) for general API resets
        ticket_id = "t2"
        ticket = next((t for t in self.db['tickets'] if t['id'] == ticket_id), None)
        if ticket:
            self.current_ticket = ticket
            self.agent_state["ticket_text"] = ticket["text"]
            
        return ResolveObservation(
            ticket_text=self.agent_state["ticket_text"],
            last_api_response="System initialized. Available tools: search_user, check_order, check_policy, issue_refund, escalate, reply",
            is_resolved=False,
            done=False,
            reward=0.0
        )

    def load_specific_ticket(self, ticket_id: str):
        """Helper method for local inference evaluation."""
        self.reset()
        ticket = next((t for t in self.db['tickets'] if t['id'] == ticket_id), None)
        if ticket:
            self.current_ticket = ticket
            self.agent_state["ticket_text"] = ticket["text"]

    def step(self, action: ResolveAction) -> ResolveObservation:
        self._state.step_count += 1
        tool = action.tool_name
        args = action.tool_arguments
        
        reward = 0.0
        response = ""
        done = False

        try:
            args_dict = json.loads(args) if args else {}

            if tool == "search_user":
                email = args_dict.get("email", "")
                user = next((u for u in self.db["users"].values() if u["email"] == email), None)
                if user:
                    response = f"Found user: {user['name']}"
                    if not self.agent_state["has_checked_user"]:
                        reward = 0.1
                        self.agent_state["has_checked_user"] = True
                else:
                    response = "User not found."
                    reward = -0.1

            elif tool == "check_policy":
                response = f"Refund Policy: {self.db['policy']['rule']}"
                if not self.agent_state["has_checked_policy"]:
                    reward = 0.2
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
                    reward = -0.5
                else:
                    response = "Refund issued successfully."
                    done = True
                    self.agent_state["is_resolved"] = True
                    
            elif tool == "escalate":
                response = "Ticket escalated to human support."
                done = True
                self.agent_state["is_resolved"] = True

            elif tool == "reply":
                response = f"Message sent to customer: {args_dict.get('message')}"
                done = True
                self.agent_state["is_resolved"] = True

            else:
                response = f"Unknown tool: {tool}"
                reward = -0.1

        except Exception as e:
            response = f"System Error processing action: {str(e)}"
            reward = -0.2

        self.agent_state["last_api_response"] = response

        # Add the final task completion grade to the reward if done
        if done:
            reward += self.grade()

        return ResolveObservation(
            ticket_text=self.agent_state["ticket_text"],
            last_api_response=response,
            is_resolved=done,
            done=done,
            reward=reward,
            metadata={"step": self._state.step_count}
        )

    @property
    def state(self) -> State:
        return self._state

    def grade(self):
        if not self.current_ticket:
            return 0.0
        ticket_id = self.current_ticket["id"]
        
        if ticket_id == "t1" and self.agent_state["is_resolved"] and "Message sent" in self.agent_state["last_api_response"]:
            return 1.0
        elif ticket_id == "t2" and self.agent_state["is_resolved"] and "Refund issued" in self.agent_state["last_api_response"]:
            return 1.0
        elif ticket_id == "t3" and self.agent_state["is_resolved"]:
            if "escalated" in self.agent_state["last_api_response"].lower():
                return 1.0
            elif "Refund issued" in self.agent_state["last_api_response"]:
                return 0.0 # Failed the trap
        return 0.0