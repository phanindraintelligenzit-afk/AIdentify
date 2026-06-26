"""Main entry point for the AI Agent Security Firewall."""

import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="AI Agent Security Firewall")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--config", default="config/settings.yaml", help="Path to config file")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker processes")
    args = parser.parse_args()

    import uvicorn
    from src.api.app import app

    uvicorn.run(
        "src.api.app:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
