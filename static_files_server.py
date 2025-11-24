#!/usr/bin/env python3
# Source: 11_examples/11_01_by-feature.md

# static_files_server.py - Serve static files alongside agents
#
# Static files directory layout:
#   This script expects a "web/" directory in the same folder:
#
#   code/11_examples/
#   ├── static_files_server.py
#   └── web/
#       ├── index.html      -> served at /
#       ├── styles.css      -> served at /styles.css
#       └── app.js          -> served at /app.js
#
# Route priority:
#   /support/*  -> SupportAgent
#   /sales/*    -> SalesAgent
#   /health     -> AgentServer health check
#   /*          -> Static files (fallback)

from signalwire_agents import AgentBase, AgentServer
from pathlib import Path

HOST = "0.0.0.0"
PORT = 3000


class SupportAgent(AgentBase):
    def __init__(self):
        super().__init__(name="support", route="/support")
        self.add_language("English", "en-US", "rime.spore")
        self.prompt_add_section("Role", "You are a support agent.")


class SalesAgent(AgentBase):
    def __init__(self):
        super().__init__(name="sales", route="/sales")
        self.add_language("English", "en-US", "rime.spore")
        self.prompt_add_section("Role", "You are a sales agent.")


def create_server():
    """Create AgentServer with static file mounting."""
    server = AgentServer(host=HOST, port=PORT)
    server.register(SupportAgent(), "/support")
    server.register(SalesAgent(), "/sales")

    # Serve static files using SDK's built-in method
    web_dir = Path(__file__).parent / "web"
    if web_dir.exists():
        server.serve_static_files(str(web_dir))

    return server


if __name__ == "__main__":
    server = create_server()
    server.run()
