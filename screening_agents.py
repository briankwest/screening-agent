#!/usr/bin/env python3
"""
Call Screening Agents - SignalWire AI Agents for Call Screening and Transfer

Two agents work together:
1. HoldAgent (/hold-agent) - Screens incoming calls, collects caller info, places on hold
2. CallAgent (/call-agent) - Receives outbound call to human, allows accept/reject

Flow:
- Caller → HoldAgent (screens) → place_call_on_hold() → dials human
- Human answers → CallAgent presents info → accept_call() bridges OR reject_call() returns to HoldAgent
"""

import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from signalwire_agents import AgentBase, AgentServer
from signalwire_agents.core.function_result import SwaigFunctionResult
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env file
load_dotenv()

# Configuration
TO_NUMBER = os.environ.get('TO_NUMBER', '+19184249378')
FROM_NUMBER = os.environ.get('FROM_NUMBER', '+12068655443')
PORT = int(os.environ.get('PORT', 5001))
HOST = os.environ.get('HOST', '0.0.0.0')
SWML_BASIC_AUTH_USER = os.environ.get('SWML_BASIC_AUTH_USER', 'signalwire')
SWML_BASIC_AUTH_PASSWORD = os.environ.get('SWML_BASIC_AUTH_PASSWORD', '')


class HoldAgent(AgentBase):
    """
    Screens incoming calls by:
    - Asking who is calling
    - Asking reason for call
    - Placing caller on hold and dialing human
    """

    def __init__(self):
        super().__init__(
            name="HoldAgent",
            route="/hold-agent"
        )

        # Configure agent
        self._configure_voice()
        self._configure_prompts()
        self._configure_tools()

    def _configure_voice(self):
        """Configure voice and speech settings."""
        self.add_language(
            name="English",
            code="en-US",
            voice="elevenlabs.josh"
        )
        self.add_hints([
            "calling", "name", "reason", "speak with", "talk to",
            "message", "callback", "available"
        ])

    def _configure_prompts(self):
        """Configure agent personality and instructions."""
        self.prompt_add_section(
            "Personality",
            "You are Ethan, a professional call screener. You are warm, efficient, and courteous. "
            "Your job is to identify callers and understand why they are calling before connecting them."
        )

        self.prompt_add_section(
            "Goal",
            "Screen incoming calls by collecting the caller's name and reason for calling, "
            "then connect them with the appropriate person."
        )

        self.prompt_add_section(
            "Instructions",
            bullets=[
                "Answer the call and greet warmly, introducing yourself as Ethan",
                "Ask for their name if not already known",
                "Ask the reason for their call",
                "Once you have both name and reason, use the place_call_on_hold function",
                "Be professional but friendly",
                "If the call returns to you after being on hold (no one available), apologize and offer to take a message"
            ]
        )

        self.prompt_add_section(
            "Greeting",
            "Always start the conversation by saying: 'Hi, this is Ethan. May I ask who's calling?'"
        )

        # Configure AI parameters
        self.set_params({
            "temperature": 0.3,
            "top_p": 0.9
        })

    def _configure_tools(self):
        """Configure SWAIG functions."""
        self.define_tool(
            name="place_call_on_hold",
            description="Place the caller on hold and dial out to connect them with a human. Use this after collecting the caller's name and reason for calling.",
            parameters={
                "type": "object",
                "properties": {
                    "caller_name": {
                        "type": "string",
                        "description": "The name of the person calling"
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason for the call"
                    }
                },
                "required": ["caller_name", "reason"]
            },
            handler=self._handle_place_call_on_hold
        )

    def _handle_place_call_on_hold(self, args, raw_data):
        """
        Place caller on hold and dial human:
        1. Extract call_id from raw_data
        2. Build dest_swml URL using SDK's get_full_url() with call info
        3. Return hold action + execute_rpc dial
        """
        call_id = raw_data.get("call_id", "unknown")
        caller_name = args.get("caller_name", "Unknown")
        reason = args.get("reason", "Unknown reason")

        # URL encode params for dest_swml
        encoded_name = urllib.parse.quote(caller_name)
        encoded_reason = urllib.parse.quote(reason)

        # Build dest_swml URL using SDK's get_full_url() which respects SWML_PROXY_URL_BASE
        # include_auth=True adds basic auth credentials to the URL
        base_url = self.get_full_url(include_auth=True).rstrip('/')
        # Replace /hold-agent with /call-agent in the URL
        base_url = base_url.replace('/hold-agent', '')
        dest_swml = f"{base_url}/call-agent?call_id={call_id}&reason={encoded_reason}&name={encoded_name}"

        return (
            SwaigFunctionResult("Please hold while I connect you with someone.")
            .hold(timeout=120)
            .add_action("swml", {
                "version": "1.0.0",
                "sections": {
                    "main": [
                        {
                            "execute_rpc": {
                                "method": "dial",
                                "params": {
                                    "devices": {
                                        "type": "phone",
                                        "params": {
                                            "to_number": TO_NUMBER,
                                            "from_number": FROM_NUMBER
                                        }
                                    },
                                    "dest_swml": dest_swml
                                }
                            }
                        }
                    ]
                }
            })
        )

    def on_swml_request(self, request_data=None, callback_path=None, request=None):
        """Set hold music URL dynamically using SDK's URL handling."""
        if request:
            # Use SDK's get_full_url() which respects SWML_PROXY_URL_BASE env var
            base_url = self.get_full_url(include_auth=False).rstrip('/')
            # Replace /hold-agent with empty to get server root
            base_url = base_url.replace('/hold-agent', '')
            hold_music_url = f"{base_url}/hold-music.wav"
            self.set_params({"hold_music": hold_music_url})

        return super().on_swml_request(request_data, callback_path, request)


class CallAgent(AgentBase):
    """
    Receives outbound call to human agent:
    - Reads call_id, reason, name from URL params
    - Greets human with caller info
    - Provides accept_call and reject_call tools
    """

    def __init__(self):
        super().__init__(
            name="CallAgent",
            route="/call-agent"
        )

        # Configure agent
        self._configure_voice()
        self._configure_prompts()
        self._configure_tools()

    def _configure_voice(self):
        """Configure voice and speech settings."""
        self.add_language(
            name="English",
            code="en-US",
            voice="elevenlabs.josh"
        )
        self.add_hints([
            "accept", "reject", "take the call", "decline",
            "message", "not available", "busy"
        ])

    def _configure_prompts(self):
        """Configure agent personality and instructions."""
        # For outbound calls, wait for user to speak first
        self.set_params({"wait_for_user": True})

        self.prompt_add_section(
            "Personality",
            "You are Ethan, a professional assistant managing incoming calls. "
            "You present caller information clearly and help the human decide whether to take the call."
        )

        self.prompt_add_section(
            "Goal",
            "Present the waiting caller's information and allow the human to accept or reject the call."
        )

        self.prompt_add_section(
            "Instructions",
            bullets=[
                "Use the exact greeting provided in the Greeting section - do not make up caller names or reasons",
                "Ask if they would like to take the call",
                "If they want to take it, use accept_call",
                "If they want to decline, ask what message to relay and use reject_call with that message",
                "Be concise and professional"
            ]
        )

        # Configure AI parameters
        self.set_params({
            "temperature": 0.3,
            "top_p": 0.9
        })

    def _configure_tools(self):
        """Configure SWAIG functions."""
        self.define_tool(
            name="accept_call",
            description="Accept the call and connect the human with the waiting caller.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._handle_accept_call
        )

        self.define_tool(
            name="reject_call",
            description="Reject the call and send a message to the waiting caller. The caller will be taken off hold and given the message.",
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to relay to the waiting caller explaining why you cannot take their call"
                    }
                },
                "required": ["message"]
            },
            handler=self._handle_reject_call
        )

    def _handle_accept_call(self, args, raw_data):
        """Accept the call - bridge human to waiting caller."""
        global_data = raw_data.get("global_data", {})
        original_call_id = global_data.get("original_call_id", "unknown")

        return (
            SwaigFunctionResult("Connecting you now.")
            .add_action("transfer", True)
            .add_action("swml", {
                "sections": {
                    "main": [
                        "answer",
                        {
                            "connect": {
                                "to": f"call:{original_call_id}",
                                "from": FROM_NUMBER
                            }
                        }
                    ]
                }
            })
        )

    def _handle_reject_call(self, args, raw_data):
        """Reject the call - send message to caller and unhold them."""
        global_data = raw_data.get("global_data", {})
        original_call_id = global_data.get("original_call_id", "unknown")
        message = args.get("message", "I apologize, but no one is available to take your call right now. Please leave a message.")

        return (
            SwaigFunctionResult("Understood, I'll let them know.")
            .add_action("swml", {
                "version": "1.0.0",
                "sections": {
                    "main": [
                        {
                            "execute_rpc": {
                                "call_id": original_call_id,
                                "method": "ai_message",
                                "params": {
                                    "role": "system",
                                    "message_text": f"The person you were trying to reach is not available. Apologize to the caller and relay this message from them: '{message}'. Then offer to take a message or help in another way."
                                }
                            }
                        },
                        {
                            "execute_rpc": {
                                "call_id": original_call_id,
                                "method": "ai_unhold",
                                "params": {}
                            }
                        }
                    ]
                }
            })
        )

    def on_swml_request(self, request_data=None, callback_path=None, request=None):
        """Extract URL parameters and configure dynamic prompt."""
        if request:
            # Extract URL params from the original caller's hold agent
            original_call_id = request.query_params.get("call_id", "unknown")
            reason = urllib.parse.unquote(request.query_params.get("reason", "unknown reason"))
            name = urllib.parse.unquote(request.query_params.get("name", "unknown caller"))

            # Store in global_data so it's available in raw_data for SWAIG functions
            self.set_global_data({
                "original_call_id": original_call_id,
                "caller_name": name,
                "caller_reason": reason
            })

            # Add dynamic context to prompt
            self.prompt_add_section(
                "Current Call Context",
                f"You have {name} on hold. They are calling about: {reason}. "
                f"The original call ID is {original_call_id}."
            )

            # Set the initial greeting
            self.prompt_add_section(
                "Greeting",
                f"Always start by saying: 'Hi this is Ethan, I have {name} on the phone, they are calling about {reason}. Would you like to take this call?'"
            )

        return super().on_swml_request(request_data, callback_path, request)


def create_server():
    """Create AgentServer with both agents and static file mounting."""
    server = AgentServer(host=HOST, port=PORT)
    server.register(HoldAgent(), "/hold-agent")
    server.register(CallAgent(), "/call-agent")

    # Mount static files (hold music, index.html, etc.)
    web_dir = Path(__file__).parent / "web"
    if web_dir.exists():
        server.app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="static")

    return server


if __name__ == "__main__":
    # Determine the public URL - use SWML_PROXY_URL_BASE if set, otherwise local
    proxy_url = os.environ.get('SWML_PROXY_URL_BASE', '').rstrip('/')
    if proxy_url:
        base_url = proxy_url
    else:
        base_url = f"http://{HOST}:{PORT}"

    # Build URL with auth credentials embedded
    parsed = urllib.parse.urlparse(base_url)
    if SWML_BASIC_AUTH_PASSWORD:
        auth_url = f"{parsed.scheme}://{SWML_BASIC_AUTH_USER}:{SWML_BASIC_AUTH_PASSWORD}@{parsed.netloc}"
    else:
        auth_url = base_url

    print("=" * 60)
    print("Call Screening Agents - SignalWire AI")
    print("=" * 60)
    print(f"\nServer: http://{HOST}:{PORT}")
    if proxy_url:
        print(f"Public URL: {proxy_url}")
    print(f"\nEndpoints (with auth):")
    print(f"  Hold Agent:  {auth_url}/hold-agent")
    print(f"  Call Agent:  {auth_url}/call-agent")
    print(f"\nEndpoints (no auth):")
    print(f"  Hold Music:  {base_url}/hold-music.wav")
    print(f"  Web UI:      {base_url}/")
    print(f"\nConfiguration:")
    print(f"  TO_NUMBER:   {TO_NUMBER}")
    print(f"  FROM_NUMBER: {FROM_NUMBER}")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")

    server = create_server()
    server.run()
