from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import ResolveAction, ResolveObservation
except ImportError:
    from models import ResolveAction, ResolveObservation

class ResolveEnvClient(EnvClient[ResolveAction, ResolveObservation, State]):
    """Client for the Resolve Environment via WebSocket/HTTP."""

    def _step_payload(self, action: ResolveAction) -> Dict:
        return {
            "tool_name": action.tool_name,
            "tool_arguments": action.tool_arguments,
        }

    def _parse_result(self, payload: Dict) -> StepResult[ResolveObservation]:
        obs_data = payload.get("observation", {})
        observation = ResolveObservation(
            ticket_text=obs_data.get("ticket_text", ""),
            last_api_response=obs_data.get("last_api_response", ""),
            is_resolved=obs_data.get("is_resolved", False),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )