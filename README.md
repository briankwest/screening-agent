# Call Screening Agents

A dual SignalWire AI Agent system for intelligent call screening and transfer. Two AI agents work together to screen incoming calls, collect caller information, and seamlessly connect callers with human agents.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CALL SCREENING SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐          ┌──────────────┐          ┌──────────────┐          │
│   │  Caller  │ ──────▶  │  HoldAgent   │ ──────▶  │  CallAgent   │          │
│   │          │          │  /hold-agent │          │  /call-agent │          │
│   └──────────┘          └──────────────┘          └──────────────┘          │
│        │                       │                         │                  │
│        │                       │                         │                  │
│        │    "Hi, this is       │    Dials human &        │    "Hi, I have   │
│        │     Ethan..."         │    places caller        │     John on the  │
│        │                       │    on hold              │     phone..."    │
│        │                       │                         │                  │
│        ▼                       ▼                         ▼                  │
│   ┌──────────┐          ┌──────────────┐          ┌──────────────┐          │
│   │ Provides │          │   On Hold    │          │    Human     │          │
│   │ name &   │          │  (120 sec)   │          │   Decides    │          │
│   │ reason   │          │  with music  │          │              │          │
│   └──────────┘          └──────────────┘          └──────────────┘          │
│                                                     /          \            │
│                                                    /            \           │
│                                            ACCEPT               REJECT      │
│                                              │                     │        │
│                                              ▼                     ▼        │
│                                       ┌──────────┐          ┌──────────┐    │
│                                       │  Bridge  │          │  Relay   │    │
│                                       │  Calls   │          │  Message │    │
│                                       └──────────┘          └──────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Intelligent Call Screening**: AI agent (Ethan) greets callers and collects their name and reason for calling
- **Hold with Music**: Callers are placed on hold with custom music while the human is contacted
- **Outbound Notification**: System automatically dials the human agent and presents caller information
- **Accept/Reject Flow**: Human can accept (bridge calls) or reject (send message back to caller)
- **Graceful Fallback**: If human doesn't answer or rejects, caller is returned to AI with a personalized message
- **120-Second Hold Timeout**: Automatic return to AI if no response within timeout period

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVER (Port 5001)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐         │
│  │        HoldAgent            │    │        CallAgent            │         │
│  │        /hold-agent          │    │        /call-agent          │         │
│  ├─────────────────────────────┤    ├─────────────────────────────┤         │
│  │                             │    │                             │         │
│  │  SWAIG Functions:           │    │  SWAIG Functions:           │         │
│  │  • place_call_on_hold()     │    │  • accept_call()            │         │
│  │                             │    │  • reject_call()            │         │
│  │                             │    │                             │         │
│  │  Prompts:                   │    │  Prompts:                   │         │
│  │  • Personality (Ethan)      │    │  • Personality (Ethan)      │         │
│  │  • Goal (screen calls)      │    │  • Goal (present info)      │         │
│  │  • Instructions             │    │  • Instructions             │         │
│  │  • Greeting                 │    │  • Greeting (dynamic)       │         │
│  │                             │    │  • Current Call Context     │         │
│  └─────────────────────────────┘    └─────────────────────────────┘         │
│                                                                             │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐         │
│  │     Static Files            │    │     Health Endpoints        │         │
│  │     /hold-music.wav         │    │     /health                 │         │
│  │     /index.html             │    │     /ready                  │         │
│  └─────────────────────────────┘    └─────────────────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Call Flow

```
                                    INCOMING CALL
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PHASE 1: SCREENING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    Caller ─────────────────▶ HoldAgent (/hold-agent)                        │
│                                    │                                        │
│                                    ▼                                        │
│                         "Hi, this is Ethan.                                 │
│                          May I ask who's calling?"                          │
│                                    │                                        │
│                                    ▼                                        │
│                            Caller: "John Smith"                             │
│                                    │                                        │
│                                    ▼                                        │
│                         "And what is this                                   │
│                          call regarding?"                                   │
│                                    │                                        │
│                                    ▼                                        │
│                         Caller: "Billing question"                          │
│                                    │                                        │
│                                    ▼                                        │
│                         place_call_on_hold(                                 │
│                           caller_name="John Smith",                         │
│                           reason="Billing question"                         │
│                         )                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PHASE 2: HOLD & DIAL                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    SWAIG Response Actions:                                                  │
│                                                                             │
│    1. hold(timeout=120)                                                     │
│       └── Caller hears hold music (hold-music.wav)                          │
│                                                                             │
│    2. execute_rpc: dial                                                     │
│       ├── to_number: TO_NUMBER (human's phone)                              │
│       ├── from_number: FROM_NUMBER                                          │
│       └── dest_swml: https://user:pass@host/call-agent                      │
│                      ?call_id={original_call_id}                            │
│                      &reason=Billing%20question                             │
│                      &name=John%20Smith                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 3: HUMAN NOTIFICATION                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    Human's Phone Rings ◀─────── Outbound Call                               │
│           │                                                                 │
│           ▼                                                                 │
│    Human Answers                                                            │
│           │                                                                 │
│           ▼                                                                 │
│    CallAgent (/call-agent?call_id=...&reason=...&name=...)                  │
│           │                                                                 │
│           ▼                                                                 │
│    on_swml_request() extracts URL params:                                   │
│    ├── original_call_id = "abc-123"                                         │
│    ├── caller_name = "John Smith"                                           │
│    └── caller_reason = "Billing question"                                   │
│           │                                                                 │
│           ▼                                                                 │
│    set_global_data({                                                        │
│      "original_call_id": "abc-123",                                         │
│      "caller_name": "John Smith",                                           │
│      "caller_reason": "Billing question"                                    │
│    })                                                                       │
│           │                                                                 │
│           ▼                                                                 │
│    "Hi this is Ethan, I have John Smith on the phone,                       │
│     they are calling about Billing question.                                │
│     Would you like to take this call?"                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                         │
                            ┌────────────┴────────────┐
                            ▼                         ▼
┌──────────────────────────────────────┐ ┌──────────────────────────────────────┐
│        PHASE 4A: ACCEPT              │ │        PHASE 4B: REJECT              │
├──────────────────────────────────────┤ ├──────────────────────────────────────┤
│                                      │ │                                      │
│  Human: "Yes, put them through"      │ │  Human: "No, tell them I'm           │
│              │                       │ │          in a meeting"               │
│              ▼                       │ │              │                       │
│       accept_call()                  │ │              ▼                       │
│              │                       │ │       reject_call(                   │
│              ▼                       │ │         message="I'm in a meeting"   │
│  SWAIG Response:                     │ │       )                              │
│  ├── transfer: true                  │ │              │                       │
│  └── swml:                           │ │              ▼                       │
│        connect:                      │ │  SWAIG Response:                     │
│          to: "call:{call_id}"        │ │  └── swml:                           │
│          from: FROM_NUMBER           │ │        execute_rpc (ai_message):     │
│              │                       │ │          call_id: {original_call_id} │
│              ▼                       │ │          message: "The person you    │
│  ┌───────────────────────┐           │ │            were trying to reach..."  │
│  │   CALLS BRIDGED       │           │ │        execute_rpc (ai_unhold):      │
│  │                       │           │ │          call_id: {original_call_id} │
│  │  Caller ◀────▶ Human  │           │ │              │                       │
│  │                       │           │ │              ▼                       │
│  └───────────────────────┘           │ │  ┌───────────────────────┐           │
│                                      │ │  │  CALLER RETURNED TO   │           │
│                                      │ │  │  HOLDAGENT WITH MSG   │           │
│                                      │ │  │                       │           │
│                                      │ │  │  "I'm sorry, they're  │           │
│                                      │ │  │   in a meeting..."    │           │
│                                      │ │  └───────────────────────┘           │
│                                      │ │                                      │
└──────────────────────────────────────┘ └──────────────────────────────────────┘
```

### Timeout Scenario

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 4C: TIMEOUT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    120 seconds elapsed...                                                   │
│           │                                                                 │
│           ▼                                                                 │
│    Hold automatically releases                                              │
│           │                                                                 │
│           ▼                                                                 │
│    Caller returns to HoldAgent                                              │
│           │                                                                 │
│           ▼                                                                 │
│    HoldAgent (per instructions):                                            │
│    "I apologize, but I wasn't able to reach anyone.                         │
│     Would you like to leave a message?"                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- SignalWire account with AI Agent access
- Phone number configured in SignalWire

### Setup

1. **Clone the repository**
   ```bash
   cd holdtransfer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `5001` | Server port (5001 avoids macOS AirPlay conflict) |
| `HOST` | No | `0.0.0.0` | Server host |
| `TO_NUMBER` | Yes | - | Human agent's phone number to dial |
| `FROM_NUMBER` | Yes | - | Caller ID for outbound calls |
| `SWML_BASIC_AUTH_USER` | No | `signalwire` | Basic auth username for SWML URLs |
| `SWML_BASIC_AUTH_PASSWORD` | Yes | - | Basic auth password for SWML URLs |

### Example `.env`

```bash
PORT=5001
HOST=0.0.0.0
TO_NUMBER=+15551234567
FROM_NUMBER=+15559876543
SWML_BASIC_AUTH_USER=signalwire
SWML_BASIC_AUTH_PASSWORD=your_secure_password
```

## Usage

### Running the Server

```bash
python screening_agents.py
```

Output:
```
============================================================
📞 Call Screening Agents - SignalWire AI
============================================================

Server: http://0.0.0.0:5001

Endpoints:
  Hold Agent:  http://0.0.0.0:5001/hold-agent
  Call Agent:  http://0.0.0.0:5001/call-agent
  Hold Music:  http://0.0.0.0:5001/hold-music.wav

Configuration:
  TO_NUMBER:   +15551234567
  FROM_NUMBER: +15559876543
============================================================

Press Ctrl+C to stop
```

### SignalWire Configuration

1. Configure your SignalWire phone number to point to your server:
   ```
   SWML Webhook URL: https://your-domain.com/hold-agent
   Method: POST
   ```

2. Ensure your server is publicly accessible (use ngrok for local development):
   ```bash
   ngrok http 5001
   ```

## API Endpoints

### HoldAgent (`/hold-agent`)

**Purpose**: Receives incoming calls, screens callers, initiates transfer

**SWML Webhook**: `POST /hold-agent`

**SWAIG Function**: `place_call_on_hold`
- Parameters:
  - `caller_name` (string, required): Name of the caller
  - `reason` (string, required): Reason for the call
- Actions:
  - Places call on hold (120s timeout)
  - Dials human via `execute_rpc`

### CallAgent (`/call-agent`)

**Purpose**: Handles outbound call to human, allows accept/reject

**SWML Webhook**: `POST /call-agent?call_id=...&reason=...&name=...`

**SWAIG Functions**:

1. `accept_call`
   - Parameters: None
   - Actions:
     - Sets `transfer: true`
     - Connects to original caller via SWML `connect`

2. `reject_call`
   - Parameters:
     - `message` (string, required): Message to relay to caller
   - Actions:
     - Sends `ai_message` to original call
     - Sends `ai_unhold` to release caller

### Static Files

- `GET /hold-music.wav` - Hold music audio
- `GET /` - Landing page (index.html)

### Health Checks

- `GET /health` - Returns `{"status": "healthy", "agents": ["HoldAgent", "CallAgent"]}`
- `GET /ready` - Returns `{"status": "ready", "agents": ["HoldAgent", "CallAgent"]}`

## Testing

### SWAIG Function Tests

Run the test script to verify all SWAIG functions:

```bash
./test_swaig_functions.sh
```

Or test individually:

```bash
# List tools
swaig-test screening_agents.py --agent-class HoldAgent --list-tools
swaig-test screening_agents.py --agent-class CallAgent --list-tools

# Test place_call_on_hold
swaig-test screening_agents.py --agent-class HoldAgent \
  --exec place_call_on_hold \
  --caller_name "John Smith" \
  --reason "billing question"

# Test accept_call
swaig-test screening_agents.py --agent-class CallAgent \
  --custom-data '{"global_data": {"original_call_id": "test-123"}}' \
  --exec accept_call

# Test reject_call
swaig-test screening_agents.py --agent-class CallAgent \
  --custom-data '{"global_data": {"original_call_id": "test-123"}}' \
  --exec reject_call \
  --message "I am in a meeting"
```

## File Structure

```
holdtransfer/
├── screening_agents.py      # Main application (both agents)
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration (not in git)
├── .env.example             # Environment template
├── test_swaig_functions.sh  # SWAIG function test script
├── web/
│   ├── hold-music.wav       # Hold music audio file
│   └── index.html           # Landing page
├── CLAUDE.md                # Claude Code instructions
├── PLAN.md                  # Implementation plan
└── README.md                # This file
```

## SWML Response Examples

### place_call_on_hold Response

```json
{
  "response": "Please hold while I connect you with someone.",
  "action": [
    {"hold": 120},
    {
      "swml": {
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
                      "to_number": "+15551234567",
                      "from_number": "+15559876543"
                    }
                  },
                  "dest_swml": "https://signalwire:pass@host.com/call-agent?call_id=abc-123&reason=billing&name=John"
                }
              }
            }
          ]
        }
      }
    }
  ]
}
```

### accept_call Response

```json
{
  "response": "Connecting you now.",
  "action": [
    {"transfer": true},
    {
      "swml": {
        "sections": {
          "main": [
            "answer",
            {
              "connect": {
                "to": "call:abc-123",
                "from": "+15559876543"
              }
            }
          ]
        }
      }
    }
  ]
}
```

### reject_call Response

```json
{
  "response": "Understood, I'll let them know.",
  "action": [
    {
      "swml": {
        "version": "1.0.0",
        "sections": {
          "main": [
            {
              "execute_rpc": {
                "call_id": "abc-123",
                "method": "ai_message",
                "params": {
                  "role": "system",
                  "message_text": "The person you were trying to reach is not available. Apologize to the caller and relay this message from them: 'I am in a meeting'. Then offer to take a message or help in another way."
                }
              }
            },
            {
              "execute_rpc": {
                "call_id": "abc-123",
                "method": "ai_unhold",
                "params": {}
              }
            }
          ]
        }
      }
    }
  ]
}
```

## Voice Configuration

Both agents use ElevenLabs Josh voice:
```python
self.add_language(
    name="English",
    code="en-US",
    voice="elevenlabs.josh"
)
```

## Customization

### Change Hold Timeout

Edit `screening_agents.py` line 135:
```python
result.hold(timeout=180)  # Change to desired seconds (max 900)
```

### Change Hold Music

Replace `web/hold-music.wav` with your audio file (WAV format recommended).

### Modify Agent Personality

Edit the prompt sections in `HoldAgent.__init__()` or `CallAgent.__init__()`:
```python
self.prompt_add_section(
    "Personality",
    "Your custom personality description..."
)
```

## Troubleshooting

### Hold Not Working
- Verify timeout is between 0-900 seconds
- Check SignalWire logs for SWAIG errors

### Outbound Call Not Connecting
- Verify `TO_NUMBER` and `FROM_NUMBER` are valid
- Check `SWML_BASIC_AUTH_PASSWORD` is set correctly
- Ensure CallAgent URL is accessible from SignalWire

### Caller Not Returned After Reject
- Verify `original_call_id` is being passed correctly in global_data
- Check `ai_unhold` RPC is being sent

## License

MIT License - see [LICENSE](LICENSE) file for details.

Built with the SignalWire AI Agents SDK.

## Support

- SignalWire AI Agents SDK: https://developer.signalwire.com/sdks/agents-sdk
- SignalWire Documentation: https://developer.signalwire.com/
- SignalWire Support: support@signalwire.com
