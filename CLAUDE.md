# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dual SignalWire AI Agent system for call screening and transfer:
1. **HoldAgent** - Screens incoming calls, collects caller info, places on hold, dials human
2. **CallAgent** - Receives outbound call to human, presents caller info, allows accept/reject

## Development Commands

```bash
# Install dependencies (use venv)
pip install -r requirements.txt

# Run the agents
python screening_agents.py
```

Server runs on port 5001 by default (5000 conflicts with macOS AirPlay).

## Architecture

**Single file** (`screening_agents.py`) containing both agents:

### HoldAgent (`/hold-agent`)
- Screens incoming calls: asks name and reason for calling
- `place_call_on_hold()` SWAIG function:
  - Places caller on hold (120s timeout)
  - Executes `dial` RPC to call human with `dest_swml` pointing to CallAgent
  - URL params passed: `call_id`, `reason`, `name` (URL encoded)

### CallAgent (`/call-agent`)
- Receives outbound call to human agent
- Parses URL params in `on_swml_request()` to get caller context
- Stores context in `global_data` for SWAIG function access
- Greets: "Hi this is Ethan, I have {name} on the phone, calling about {reason}"
- `accept_call()` - Returns SWML with `connect` to bridge human to waiting caller
- `reject_call(message)` - Sends `ai_message` + `ai_unhold` RPCs to return caller to HoldAgent

### Call Flow
```
Caller → HoldAgent (screens) → place_call_on_hold()
                                  ├── hold(120s)
                                  └── dial RPC → human phone
                                                    ↓
                              CallAgent receives call with URL params
                                  ├── accept_call() → connect to call:{id}
                                  └── reject_call() → ai_message + ai_unhold
```

## Key Endpoints

- `POST /hold-agent` - SWML webhook for incoming calls
- `POST /call-agent` - SWML webhook for outbound call to human
- `GET /hold-music.wav` - Hold music audio file
- `GET /health`, `GET /ready` - Health check endpoints

## Configuration

Environment variables (see `.env.example`):
- `PORT` (default: 5001), `HOST` (default: 0.0.0.0)
- `TO_NUMBER` - Human agent's phone number to dial
- `FROM_NUMBER` - Caller ID for outbound calls and connect actions
- `SWML_BASIC_AUTH_USER`, `SWML_BASIC_AUTH_PASSWORD` - Auth for dest_swml URLs

## SignalWire SDK Patterns

### SWAIG Functions with Actions
```python
@self.tool(name="function_name", description="...", parameters={...})
def function_name(args, raw_data):
    result = SwaigFunctionResult("response text")
    result.hold(timeout=120)
    result.add_action("swml", {...})  # Full SWML for execute_rpc
    result.add_action("transfer", True)
    return result
```

### Dynamic Prompt from URL Params
```python
def on_swml_request(self, request_data, callback_path, request):
    call_id = request.query_params.get("call_id")
    # Store in global_data for SWAIG function access
    self.set_global_data({"original_call_id": call_id, ...})
    self.prompt_add_section("Greeting", f"Hi, I have {name} on the phone...")
    return super().on_swml_request(request_data, callback_path, request)
```

### Key RPC Methods (wrapped in SWML)
- `dial` with `dest_swml` - Outbound call with SWML endpoint
- `ai_message` - Send message to AI on another call
- `ai_unhold` - Release a call from hold

Access call data from `raw_data`: `call_id`, `caller_id_name`, `caller_id_num`, `global_data`

## Testing

```bash
# Run SWAIG function tests
./test_swaig_functions.sh

# Or individually
swaig-test screening_agents.py --agent-class HoldAgent --list-tools
swaig-test screening_agents.py --agent-class CallAgent --exec accept_call
```
