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

# --- THE FIX: Create an explicit endpoint for the Docker Healthcheck ---
@app.get("/health")
def health_check():
    return {"status": "healthy"}