"""Refreshing model prices from a public list, with a preview and an explicit confirmation.

Two fixed sources, nothing configurable and no credentials: the LiteLLM price list (checked
against the current file: per-token USD in `input_cost_per_token`, `output_cost_per_token`,
`cache_read_input_token_cost`, `cache_creation_input_token_cost`) and, if that fails, the
OpenRouter model list (`pricing.prompt` / `completion` / `input_cache_read` / `input_cache_write`,
USD per token as strings). Both are converted to USD per 1M tokens.

A model is matched by its exact name or with a provider prefix as the list spells it
("gemini/gemini-3.6-flash"); nothing is guessed from an arbitrary prefix. `preview()` changes
nothing; `apply()` writes only what the user selected, from the preview kept on the server
(10 minutes), never prices sent by the browser.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import logging
import math
import threading
import time
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from .usage import PRICE_KEYS, find_price

LITELLM_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/models"
ALLOWED_URLS = frozenset({LITELLM_URL, OPENROUTER_URL})
FETCH_TIMEOUT_SECONDS = 20.0
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
PREVIEW_TTL_SECONDS = 600
MAX_PREVIEWS = 5
# A new price more than this many times (or less than 1/this) the current one is probably a
# mismatch of models: shown with a warning and not selected by default.
SUSPICIOUS_RATIO = 2.0

Fetcher = Callable[[str, float, int], "tuple[int, bytes]"]


class PriceListError(Exception):
    def __init__(self, message: str, http_status: int = 502, code: str = "price_list_error"):
        super().__init__(message)
        self.http_status = http_status
        self.code = code


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # a redirect would leave the fixed URL
        return None


def default_fetch(url: str, timeout: float, max_bytes: int) -> tuple[int, bytes]:
    """GET one of the two fixed URLs: no redirects, no cookies or keys, at most max_bytes."""
    if url not in ALLOWED_URLS:
        raise PriceListError("Це джерело цін не дозволене.", 400, "price_source_forbidden")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "translation-workbench"})
    try:
        with build_opener(_NoRedirect).open(request, timeout=timeout) as response:
            data = response.read(max_bytes + 1)
            status = response.status
    except HTTPError as error:
        return error.code, b""
    except (URLError, TimeoutError, OSError) as error:
        raise PriceListError("Не вдалося з’єднатися з джерелом цін (або час очікування вичерпано).") from error
    if len(data) > max_bytes:
        raise PriceListError("Відповідь джерела цін завелика.")
    return status, data


# --- parsing --------------------------------------------------------------------------------


def _per_mtok(value: Any) -> float | None:
    """USD per token (number or numeric string) -> USD per 1M tokens; None when absent or invalid."""
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not amount.is_finite() or amount < 0:
        return None
    result = float(amount * 1_000_000)
    return round(result, 6) if math.isfinite(result) else None


def _entry(input_cost: Any, output_cost: Any, cache_read: Any, cache_write: Any) -> dict[str, float | None] | None:
    entry = {
        "inputPerMTok": _per_mtok(input_cost),
        "outputPerMTok": _per_mtok(output_cost),
        "cacheReadPerMTok": _per_mtok(cache_read),
        "cacheWritePerMTok": _per_mtok(cache_write),
    }
    if entry["inputPerMTok"] is None or entry["outputPerMTok"] is None:
        return None
    if entry["inputPerMTok"] == 0 and entry["outputPerMTok"] == 0:  # placeholders such as sample_spec
        return None
    return entry


def parse_litellm(payload: Any) -> dict[str, dict[str, float | None]]:
    if not isinstance(payload, dict):
        raise PriceListError("Список цін LiteLLM має неочікуваний формат.")
    catalog = {}
    for key, item in payload.items():
        if key == "sample_spec" or not isinstance(item, dict) or not isinstance(key, str):
            continue
        entry = _entry(item.get("input_cost_per_token"), item.get("output_cost_per_token"),
                       item.get("cache_read_input_token_cost"), item.get("cache_creation_input_token_cost"))
        if entry:
            catalog[key] = entry
    if not catalog:
        raise PriceListError("У списку цін LiteLLM не знайдено жодної моделі з цінами.")
    return catalog


def parse_openrouter(payload: Any) -> dict[str, dict[str, float | None]]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        raise PriceListError("Список моделей OpenRouter має неочікуваний формат.")
    catalog = {}
    for item in data:
        pricing = item.get("pricing") if isinstance(item, dict) else None
        if not isinstance(pricing, dict) or not isinstance(item.get("id"), str):
            continue
        entry = _entry(pricing.get("prompt"), pricing.get("completion"),
                       pricing.get("input_cache_read"), pricing.get("input_cache_write"))
        if entry:
            catalog[item["id"]] = entry
    if not catalog:
        raise PriceListError("У списку OpenRouter не знайдено жодної моделі з цінами.")
    return catalog


SOURCES = (
    {"id": "litellm", "name": "список LiteLLM", "url": LITELLM_URL, "parse": parse_litellm},
    {"id": "openrouter", "name": "OpenRouter", "url": OPENROUTER_URL, "parse": parse_openrouter},
)

# --- matching -------------------------------------------------------------------------------

# Provider prefixes as the lists spell them. For Gemini the API we call is "gemini/...".
_PREFIXES = {
    "gemini": ("gemini/", ""),
    "openai": ("", "openai/"),
    "claude": ("", "anthropic/"),
    "grok": ("", "xai/"),
}
_ANY_PREFIX = ("", "openai/", "gemini/", "anthropic/", "xai/")


def infer_engine(model: str) -> str | None:
    name = model.lower().removeprefix("models/")
    for prefix, engine in (("claude", "claude"), ("gemini", "gemini"), ("grok", "grok"),
                           ("gpt", "openai"), ("chatgpt", "openai"), ("o1", "openai"), ("o3", "openai"), ("o4", "openai")):
        if name.startswith(prefix):
            return engine
    return None


def match_model(model: str, engine: str | None, catalog: Mapping[str, Mapping[str, Any]]) -> tuple[str, Mapping[str, Any]] | None:
    """(list key, prices) for an exact name or a provider-prefixed name; nothing else.

    The Gemini API we call is priced under "gemini/<name>" in the lists, so that key comes
    first for Gemini; for the others the bare name comes first."""
    name = model.removeprefix("models/")
    resolved = engine if engine in _PREFIXES else infer_engine(name)
    if resolved == "gemini":
        candidates = [f"gemini/{name}", name]
    elif resolved in _PREFIXES:
        candidates = [name] + [prefix + name for prefix in _PREFIXES[resolved] if prefix]
    else:
        candidates = [name] + [prefix + name for prefix in _ANY_PREFIX if prefix]
    for key in dict.fromkeys(candidates):
        if key in catalog:
            return key, catalog[key]
    return None


def _same(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    for key in PRICE_KEYS:
        a, b = left.get(key), right.get(key)
        if (a is None) != (b is None) or (a is not None and not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)):
            return False
    return True


def _suspicious(current: Mapping[str, Any] | None, proposed: Mapping[str, Any]) -> bool:
    if current is None:
        return False
    for key in PRICE_KEYS:
        old, new = current.get(key), proposed.get(key)
        if old and new and (new > old * SUSPICIOUS_RATIO or new < old / SUSPICIOUS_RATIO):
            return True
    return False


# --- the service ----------------------------------------------------------------------------

_PREVIEWS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PriceListService:
    def __init__(self, storage: Any, fetcher: Fetcher = default_fetch, clock: Callable[[], float] = time.time):
        self._storage = storage
        self._fetcher = fetcher
        self._clock = clock

    # fetching
    def _load_catalog(self) -> tuple[dict[str, Any], dict[str, dict[str, float | None]]]:
        problems = []
        for index, source in enumerate(SOURCES):
            try:
                status, body = self._fetcher(source["url"], FETCH_TIMEOUT_SECONDS, MAX_RESPONSE_BYTES)
                if status != 200:
                    raise PriceListError(f"Джерело {source['name']} відповіло HTTP {status}.")
                if len(body) > MAX_RESPONSE_BYTES:
                    raise PriceListError(f"Відповідь джерела {source['name']} завелика.")
                try:
                    payload = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise PriceListError(f"Джерело {source['name']} повернуло не JSON.") from error
                catalog = source["parse"](payload)
            except PriceListError as error:
                logging.warning("Price list %s failed: %s", source["url"], error)
                problems.append(str(error))
                continue
            info = {"id": source["id"], "name": source["name"], "url": source["url"], "fetchedAt": _now_iso(), "fallback": index > 0}
            return info, catalog
        raise PriceListError("Не вдалося отримати список цін. " + " ".join(problems))

    # preview
    def preview(self) -> dict[str, Any]:
        """The comparison «було → стане»; writes nothing."""
        source, catalog = self._load_catalog()
        prices = self._storage.list_model_prices()
        targets: dict[str, str | None] = {model: infer_engine(model) for model in prices}
        for row in self._storage.list_translation_usage_all():
            model = row["model"]
            if model and model not in targets and find_price(model, prices) is None:
                targets[model] = row["engine"]
            elif model in targets and targets[model] is None:
                targets[model] = row["engine"]
        items = []
        proposals: dict[str, dict[str, Any]] = {}
        for model, engine in sorted(targets.items()):
            current = prices.get(model)
            matched = match_model(model, engine, catalog)
            item: dict[str, Any] = {
                "model": model, "engine": engine, "matchedKey": None, "current": current, "proposed": None,
                "status": "not_found", "protectedManual": bool(current and current["source"] == "manual"),
                "suspicious": False, "defaultSelected": False,
            }
            if matched:
                key, listed = matched
                proposed = {price_key: (listed.get(price_key) if listed.get(price_key) is not None
                                        else (current or {}).get(price_key)) for price_key in PRICE_KEYS}
                item["matchedKey"] = key
                item["proposed"] = proposed
                if current is not None and _same(current, proposed):
                    item["status"] = "same"
                else:
                    item["status"] = "changed" if current is not None else "new"
                    item["suspicious"] = _suspicious(current, proposed)
                    item["defaultSelected"] = not item["suspicious"] and not item["protectedManual"]
                    proposals[model] = proposed
            items.append(item)
        order = {"changed": 0, "new": 1, "same": 2, "not_found": 3}
        items.sort(key=lambda entry: (order[entry["status"]], entry["model"]))
        preview_id = uuid4().hex
        with _LOCK:
            self._purge()
            while len(_PREVIEWS) >= MAX_PREVIEWS:
                _PREVIEWS.pop(min(_PREVIEWS, key=lambda key: _PREVIEWS[key]["createdAt"]))
            _PREVIEWS[preview_id] = {"createdAt": self._clock(), "proposals": proposals, "source": source}
        return {"previewId": preview_id, "source": source, "items": items, "expiresInSeconds": PREVIEW_TTL_SECONDS}

    def _purge(self) -> None:
        now = self._clock()
        for key in [key for key, value in _PREVIEWS.items() if now - value["createdAt"] > PREVIEW_TTL_SECONDS]:
            del _PREVIEWS[key]

    # apply
    def apply(self, preview_id: Any, models: Any, overwrite_manual: Any) -> dict[str, Any]:
        """Write the selected models of a preview. Manual prices only with overwrite_manual."""
        if not isinstance(models, list) or not all(isinstance(model, str) for model in models):
            raise PriceListError("Оберіть моделі зі списку.", 400, "price_apply_invalid")
        with _LOCK:
            self._purge()
            preview = _PREVIEWS.get(preview_id) if isinstance(preview_id, str) else None
        if preview is None:
            raise PriceListError("Порівняння застаріло (діє 10 хвилин). Натисніть «Оновити ціни» ще раз.", 409, "price_preview_expired")
        updates = {model: preview["proposals"][model] for model in dict.fromkeys(models) if model in preview["proposals"]}
        unknown = [model for model in dict.fromkeys(models) if model not in preview["proposals"]]
        applied, skipped = self._storage.apply_list_prices(updates, bool(overwrite_manual))
        if applied:
            self._storage.set_setting("prices_updated_at", _now_iso())
            self._storage.set_setting("prices_updated_source", json.dumps({"id": preview["source"]["id"], "name": preview["source"]["name"], "url": preview["source"]["url"]}))
            with _LOCK:
                _PREVIEWS.pop(preview_id, None)
        return {"applied": applied, "skippedManual": skipped, "unknown": unknown, "source": preview["source"]}


__all__ = [
    "ALLOWED_URLS",
    "LITELLM_URL",
    "OPENROUTER_URL",
    "PriceListError",
    "PriceListService",
    "default_fetch",
    "infer_engine",
    "match_model",
    "parse_litellm",
    "parse_openrouter",
]
