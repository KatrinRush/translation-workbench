"""Workbench server with deterministic LLM transports for browser tests.

No request leaves the machine: connection checks, translations and model lists for
OpenAI, Claude and Gemini are answered here in each provider's wire format.
"""

import json
import re

from backend import server

E2E_MODELS = {
    "claude": [{"id": "claude-e2e-alpha", "display_name": "Claude E2E Alpha"}, {"id": "claude-e2e-beta", "display_name": "Claude E2E Beta"}],
    "openai": [{"id": "gpt-e2e-one", "object": "model"}, {"id": "text-embedding-e2e", "object": "model"}],
    "gemini": [{"name": "models/gemini-e2e", "displayName": "Gemini E2E", "supportedGenerationMethods": ["generateContent"]}],
}


def _translated_chunk(message, label):
    chunk = re.search(r"<chunk>.*</chunk>", message, re.S)
    if not chunk:
        return None
    return re.sub(r'<p id="([^"]+)">.*?</p>', lambda match: f'<p id="{match.group(1)}">{label} переклад</p>', chunk.group(0), flags=re.S)


class FakeLlmTransport:
    def __init__(self, provider_id):
        self.provider_id = provider_id

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        if self.provider_id == "openai":
            text = _translated_chunk(payload.get("input", "") if isinstance(payload.get("input"), str) else "", "GPT")
            if text is None:  # connection check / analysis
                return 200, json.dumps({"id": "resp_e2e", "model": "gpt-4.1-nano"}).encode("utf-8")
            reply = {"id": "resp_e2e", "model": payload["model"], "status": "completed",
                     "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
                     "usage": {"input_tokens": 10, "output_tokens": 5}}
        elif self.provider_id == "claude":
            text = _translated_chunk(payload["messages"][0]["content"], "Claude")
            reply = {"id": "msg_e2e", "model": payload["model"], "stop_reason": "end_turn",
                     "content": [{"type": "text", "text": text or "OK"}], "usage": {"input_tokens": 10, "output_tokens": 5}}
        else:
            text = _translated_chunk(payload["contents"][0]["parts"][0]["text"], "Gemini")
            reply = {"candidates": [{"content": {"parts": [{"text": text or "OK"}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5}}
        return 200, json.dumps(reply, ensure_ascii=False).encode("utf-8")

    def get(self, url, headers, timeout):
        if self.provider_id == "claude":
            reply = {"data": E2E_MODELS["claude"], "has_more": False}
        elif self.provider_id == "openai":
            reply = {"object": "list", "data": E2E_MODELS["openai"]}
        else:
            reply = {"models": E2E_MODELS["gemini"]}
        return 200, json.dumps(reply).encode("utf-8")


for provider_id in ("openai", "claude", "gemini"):
    server.provider_registry.get(provider_id)._transport = FakeLlmTransport(provider_id)
server.main()
