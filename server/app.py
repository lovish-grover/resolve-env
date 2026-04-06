try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv is required for the web interface.") from e

try:
    from ..models import ResolveAction, ResolveObservation
    from .resolve_environment import ResolveEnvironment
except ModuleNotFoundError:
    from models import ResolveAction, ResolveObservation
    from server.resolve_environment import ResolveEnvironment

app = create_app(
    ResolveEnvironment,
    ResolveAction,
    ResolveObservation,
    env_name="resolve",
    max_concurrent_envs=10, 
)

def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)