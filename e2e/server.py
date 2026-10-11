"""Workbench server with deterministic LLM transports for browser tests.

No request leaves the machine: connection checks, translations and model lists for
OpenAI, Claude and Gemini are answered here in each provider's wire format.
"""

import json
import re
import time

from backend import server

E2E_MODELS = {
    "claude": [{"id": "claude-e2e-alpha", "display_name": "Claude E2E Alpha"}, {"id": "claude-e2e-beta", "display_name": "Claude E2E Beta"}],
    "openai": [{"id": "gpt-e2e-one", "object": "model"}, {"id": "text-embedding-e2e", "object": "model"}],
    "gemini": [{"name": "models/gemini-e2e", "displayName": "Gemini E2E", "supportedGenerationMethods": ["generateContent"]}],
}


def _translated_chunk(message, label, version=None):
    chunk = re.search(r"<chunk>.*</chunk>", message, re.S)
    if not chunk:
        return None
    if version:
        label = f"{label} v{version}"
    return re.sub(r'<p id="([^"]+)">.*?</p>', lambda match: f'<p id="{match.group(1)}">{label} переклад</p>', chunk.group(0), flags=re.S)


class FakeLlmTransport:
    def __init__(self, provider_id):
        self.provider_id = provider_id

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        # Tests get a different answer (a new version of the variant) by putting "[[v2]]" into
        # the project's translation rules (they travel in the system prompt); without the
        # marker the answer is always the same.
        marker = re.search(r"\[\[v(\d+)\]\]", body.decode("utf-8") if isinstance(body, bytes) else str(body))
        version = marker.group(1) if marker else None
        if "[[slow]]" in (body.decode("utf-8") if isinstance(body, bytes) else str(body)):
            time.sleep(0.6)  # lets a test press Пауза / Зупинити while the queue is running
        if self.provider_id == "openai":
            text = _translated_chunk(payload.get("input", "") if isinstance(payload.get("input"), str) else "", "GPT", version)
            if text is None:  # connection check / analysis
                return 200, json.dumps({"id": "resp_e2e", "model": "gpt-4.1-nano"}).encode("utf-8")
            reply = {"id": "resp_e2e", "model": payload["model"], "status": "completed",
                     "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
                     "usage": {"input_tokens": 10, "output_tokens": 5}}
        elif self.provider_id == "claude":
            text = _translated_chunk(payload["messages"][0]["content"], "Claude", version)
            reply = {"id": "msg_e2e", "model": payload["model"], "stop_reason": "end_turn",
                     "content": [{"type": "text", "text": text or "OK"}], "usage": {"input_tokens": 10, "output_tokens": 5}}
        else:
            text = _translated_chunk(payload["contents"][0]["parts"][0]["text"], "Gemini", version)
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

# "Оновити ціни" never reaches the network here: the public price list is this small fixed one.
E2E_PRICE_LIST = {
    "sample_spec": {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0},
    "claude-sonnet-5-5": {"input_cost_per_token": 2e-06, "output_cost_per_token": 1e-05, "cache_read_input_token_cost": 1e-07, "cache_creation_input_token_cost": 2.5e-06},
    "gpt-5.5": {"input_cost_per_token": 5e-06, "output_cost_per_token": 3e-05, "cache_read_input_token_cost": 5e-07},
    "gpt-5.5-pro": {"input_cost_per_token": 3e-05, "output_cost_per_token": 0.00018},
    "gemini-3.6-flash": {"input_cost_per_token": 9e-07, "output_cost_per_token": 4e-06},
    "gemini/gemini-3.6-flash": {"input_cost_per_token": 7.5e-07, "output_cost_per_token": 3.75e-06, "cache_read_input_token_cost": 7.5e-08},
}


def fake_price_list_fetcher(url, timeout, max_bytes):
    if url == server.price_list_default_fetch.__globals__["LITELLM_URL"]:
        return 200, json.dumps(E2E_PRICE_LIST).encode("utf-8")
    return 503, b""


server.price_list_fetcher = fake_price_list_fetcher
server.main()
