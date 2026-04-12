import json
import os
import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import ResolveAction, ResolveObservation


MAX_STEPS = 8
STEP_PENALTY = 0.02


class ResolveEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        # Load DB safely
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.json")
        if not os.path.exists(db_path):
            db_path = "data.json"

        with open(db_path, "r") as f:
            self.db = json.load(f)

        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.current_ticket = None
        self.agent_state = self._blank_state()

    def _blank_state(self):
        return {
            "has_checked_user": False,
            "has_checked_policy": False,
            "has_checked_order": False,
            "is_resolved": False,
            "ticket_text": "",
            "last_api_response": "Awaiting action.",
        }

    # ---------------- RESET ---------------- #
    def reset(self) -> ResolveObservation:
        # TASK 1: strictly instantiate fresh state
        self._state = State(episode_id=str(uuid4()), step_count=0)
        # Force complete wipe
        self.agent_state = self._blank_state()

        # RANDOM TASK (IMPORTANT FOR EVAL)
        ticket = random.choice(self.db["tickets"])
        self.current_ticket = ticket

        # Add slight noise (prevents hardcoding)
        noise = f" [Ref:{random.randint(100,999)}]"
        self.agent_state["ticket_text"] = ticket["text"] + noise

        return ResolveObservation(
            ticket_text=self.agent_state["ticket_text"],
            last_api_response="System initialized. Tools: search_user, check_order, check_policy, issue_refund, escalate, reply",
            is_resolved=False,
            done=False,
            reward=0.0,
        )

    # ---------------- STEP ---------------- #
    def step(self, action: ResolveAction) -> ResolveObservation:
        self._state.step_count += 1

        tool = action.tool_name
        args = action.tool_arguments

        # TASK 3: Explicitly apply baseline cost
        reward = -STEP_PENALTY
        done = False
        response = ""

        try:
            args_dict = json.loads(args) if args else {}

            # -------- TOOL LOGIC -------- #

            if tool == "search_user":
                email = args_dict.get("email", "")
                user = next((u for u in self.db["users"].values() if u["email"] == email), None)

                if user:
                    response = f"Found user: {user['name']}"
                    if not self.agent_state["has_checked_user"]:
                        reward += 0.1
                        self.agent_state["has_checked_user"] = True
                else:
                    response = "User not found"
                    reward -= 0.1

            elif tool == "check_order":
                order_id = args_dict.get("order_id", "")
                order = self.db["orders"].get(order_id)

                if order:
                    response = f"Order status: {order['status']}, Days: {order['days_since_purchase']}"
                    if not self.agent_state["has_checked_order"]:
                        reward += 0.1
                        self.agent_state["has_checked_order"] = True
                else:
                    response = "Order not found"
                    reward -= 0.1

            elif tool == "check_policy":
                response = f"Policy: {self.db['policy']['rule']}"
                if not self.agent_state["has_checked_policy"]:
                    reward += 0.15
                    self.agent_state["has_checked_policy"] = True

            elif tool == "issue_refund":
                if not self.agent_state["has_checked_policy"]:
                    response = "BLOCKED: Must check policy first"
                    reward -= 0.5
                else:
                    response = "Refund issued successfully"
                    reward += 0.3
                    done = True
                    self.agent_state["is_resolved"] = True

            elif tool == "escalate":
                response = "Escalated to human support"
                reward += 0.2
                done = True
                self.agent_state["is_resolved"] = True

            elif tool == "reply":
                response = f"Reply sent: {args_dict.get('message', '')}"
                reward += 0.2
                done = True
                self.agent_state["is_resolved"] = True

            else:
                response = f"Unknown tool: {tool}"
                reward -= 0.1

        except Exception as e:
            response = f"System error: {str(e)}"
            reward -= 0.2

        # -------- MAX STEP CUT -------- #
        if self._state.step_count >= MAX_STEPS:
            done = True
            reward -= 0.5

        self.agent_state["last_api_response"] = response

        # -------- FINAL REWARD -------- #
        if done:
            # Capture the final action taken
            self.agent_state["final_action"] = tool
            final_score = self.grade()
            reward += final_score

        return ResolveObservation(
            ticket_text=self.agent_state["ticket_text"],
            last_api_response=response,
            is_resolved=done,
            done=done,
            reward=reward,
            metadata={"step": self._state.step_count},
        )

    # ---------------- STATE ---------------- #
    @property
    def state(self) -> State:
        return self._state

    def load_specific_ticket(self, ticket_id: str):
        """Loads a specific ticket based on task ID for deterministic evaluation."""
        ticket = next((t for t in self.db["tickets"] if t["id"] == ticket_id), None)
        if ticket:
            self.current_ticket = ticket
            self.agent_state["ticket_text"] = ticket["text"]
        else:
            raise ValueError(f"Ticket {ticket_id} not found!")

    # ---------------- GRADER ---------------- #
    def grade(self) -> float:
        """
        TASK 2: Deterministic ground-truth reward.
        Returns 1.0 for success, 0.0 for failure (score must be 0.0-1.0).
        """
        if not self.current_ticket:
            return 0.0

        expected = self.current_ticket.get("expected_outcome", "")
        action_taken = self.agent_state.get("final_action", "")

        # Map reply tool to its implicit intended outcome since standard tickets expect "inform_delayed"
        if action_taken == "reply":
            match_action = "inform_delayed"
        else:
            match_action = action_taken

        if match_action == expected:
            return 1.0
        else:
            return 0.0