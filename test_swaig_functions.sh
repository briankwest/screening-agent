#!/bin/bash
# test_swaig_functions.sh - Test all SWAIG functions for both agents

SCRIPT="screening_agents.py"

echo "=== Listing HoldAgent tools ==="
swaig-test $SCRIPT --agent-class HoldAgent --list-tools

echo ""
echo "=== Listing CallAgent tools ==="
swaig-test $SCRIPT --agent-class CallAgent --list-tools

echo ""
echo "=== Testing HoldAgent: place_call_on_hold ==="
swaig-test $SCRIPT --agent-class HoldAgent \
  --exec place_call_on_hold \
  --caller_name "John Smith" \
  --reason "billing question"

echo ""
echo "=== Testing CallAgent: accept_call ==="
swaig-test $SCRIPT --agent-class CallAgent \
  --custom-data '{"global_data": {"original_call_id": "test-call-123", "caller_name": "John Smith", "caller_reason": "billing question"}}' \
  --exec accept_call

echo ""
echo "=== Testing CallAgent: reject_call ==="
swaig-test $SCRIPT --agent-class CallAgent \
  --custom-data '{"global_data": {"original_call_id": "test-call-123", "caller_name": "John Smith", "caller_reason": "billing question"}}' \
  --exec reject_call \
  --message "I am in a meeting, please take a message"
