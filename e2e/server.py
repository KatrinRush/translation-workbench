"""Workbench server with a deterministic OpenAI transport for browser tests."""

import json

from backend import server


class FakeOpenAITransport:
    def post(self, url, headers, body, timeout):
        return 200, json.dumps({"id": "resp_e2e", "model": "gpt-4.1-nano"}).encode("utf-8")


server.provider_registry.get("openai")._transport = FakeOpenAITransport()
server.main()