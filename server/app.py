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

def main():
    # Forces Uvicorn to run on port 7860
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()