# from pydantic import BaseModel, Field

# class Action(BaseModel):
#     tool_name: str = Field(description="The name of the tool to use (e.g., 'search_user', 'check_order', 'check_policy', 'issue_refund', 'escalate', 'reply_to_customer')")
#     tool_arguments: str = Field(description="JSON formatted string of arguments for the tool.")

# class Observation(BaseModel):
#     ticket_text: str = Field(description="The original message from the customer.")
#     last_api_response: str = Field(description="The output from the last tool used.")
#     is_resolved: bool = Field(description="True if the ticket has been resolved or escalated.")

# class Reward(BaseModel):
#     step_reward: float = Field(description="The reward earned for the last action.")

from openenv.core.env_server.types import Action, Observation
from pydantic import Field

class ResolveAction(Action):
    """Action for the Resolve environment."""
    tool_name: str = Field(..., description="The name of the tool to use (e.g., 'search_user', 'check_order', 'check_policy', 'issue_refund', 'escalate', 'reply')")
    tool_arguments: str = Field(default="{}", description="JSON formatted string of arguments for the tool.")

class ResolveObservation(Observation):
    """Observation from the Resolve environment."""
    ticket_text: str = Field(default="", description="The original message from the customer.")
    last_api_response: str = Field(default="", description="The output from the last tool used.")
    is_resolved: bool = Field(default=False, description="True if the ticket has been resolved or escalated.")