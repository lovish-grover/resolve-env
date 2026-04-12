from pydantic import Field
from openenv.core.env_server.types import Action, Observation

class ResolveAction(Action):
    """
    The strictly typed action space for the ResolveEnv.
    The agent must output a valid tool name and a JSON string of arguments.
    """
    tool_name: str = Field(
        ..., 
        description="The name of the tool to use (e.g., 'search_user', 'check_order', 'check_policy', 'issue_refund', 'escalate', 'reply')."
    )
    tool_arguments: str = Field(
        ..., 
        description="A JSON-formatted string containing the arguments for the tool. Use '{}' if no arguments are required."
    )


class ResolveObservation(Observation):
    """
    The strictly typed observation space for the ResolveEnv.
    This provides the agent with the current ticket state and the result of their last tool action.
    """
    ticket_text: str = Field(
        ..., 
        description="The full text of the customer's support ticket."
    )
    last_api_response: str = Field(
        ..., 
        description="The textual result of the last tool execution, or the system initialization text."
    )
    is_resolved: bool = Field(
        default=False, 
        description="Indicates whether the ticket has been successfully resolved or correctly escalated."
    )
    done: bool = Field(
        default=False, 
        description="Indicates if the current environment episode has ended."
    )
    reward: float = Field(
        default=0.0, 
        description="The shaped reward scalar returned from the last taken action."
    )