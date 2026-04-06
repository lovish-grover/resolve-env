import uvicorn
from openenv.core.env_server.http_server import create_app

# Absolute imports to prevent Docker relative import errors
from models import ResolveAction, ResolveObservation
from server.resolve_environment import ResolveEnvironment

app = create_app(
    ResolveEnvironment,
    ResolveAction,
    ResolveObservation,
    env_name="resolve",
    max_concurrent_envs=10, 
)

def main():
    # Required by the Hackathon grader for multi-mode deployment.
    # Forces Uvicorn to run on port 7860 (Hugging Face default).
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()