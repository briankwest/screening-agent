#!/usr/bin/env python3
"""Test script for static files server with modified SDK."""

import sys
sys.path.insert(0, '/Users/brian/workdir/signalwire-agents')

from signalwire_agents import AgentBase, AgentServer
from pathlib import Path
import threading
import time
import requests
import os

class SupportAgent(AgentBase):
    def __init__(self):
        super().__init__(name='support', route='/support')
        self.add_language('English', 'en-US', 'rime.spore')
        self.prompt_add_section('Role', 'You are a support agent.')

class SalesAgent(AgentBase):
    def __init__(self):
        super().__init__(name='sales', route='/sales')
        self.add_language('English', 'en-US', 'rime.spore')
        self.prompt_add_section('Role', 'You are a sales agent.')

server = AgentServer(host='0.0.0.0', port=3000)
server.register(SupportAgent(), '/support')
server.register(SalesAgent(), '/sales')

web_dir = Path(__file__).parent / 'web'
if web_dir.exists():
    server.serve_static_files(str(web_dir))

#def test():
#    time.sleep(2)
#    for path in ['/support', '/support/', '/sales', '/sales/', '/', '/health']:
#        try:
#            r = requests.get(f'http://localhost:3000{path}', timeout=2)
#            print(f'{path}: {r.status_code}')
#        except Exception as e:
#            print(f'{path}: Error - {e}')
#    os._exit(0)

if __name__ == '__main__':
    t = threading.Thread(daemon=True)
    t.start()
    server.run()
