"""Price list refresh (mock transport only), price table rules, daily usage in a time zone, CSV."""
import csv
import io
import json
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from zoneinfo import ZoneInfo

from backend import price_list, server
from backend.price_list import (
    LITELLM_URL, OPENROUTER_URL, PriceListError, PriceListService, default_fetch, infer_engine, match_model,
    parse_litellm, parse_openrouter,
)
from backend.storage import Storage
from backend.usage import (
    DEFAULT_MODEL_PRICES, daily_report, find_price, local_date, local_day_start_utc, resolve_timezone, timezone_or_default, usage_csv,
)

KYIV = ZoneInfo("Europe/Kyiv")

LITELLM = {
    "sample_spec": {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0},
    "gpt-5.5": {"input_cost_per_token": 5e-06, "output_cost_per_token": 3e-05, "cache_read_input_token_cost": 5e-07, "cache_creation_input_token_cost": None},
    "gpt-5.5-pro": {"input_cost_per_token": 3e-05, "output_cost_per_token": 0.00018},
    "gpt-5.5-mini": {"input_cost_per_token": 5e-07, "output_cost_per_token": 3e-06},
    "claude-sonnet-5-5": {"input_cost_per_token": 2e-06, "output_cost_per_token": 1e-05, "cache_read_input_token_cost": 1e-07, "cache_creation_input_token_cost": 2.5e-06},
    "gemini-3.6-flash": {"input_cost_per_token": 9e-07, "output_cost_per_token": 4e-06},  # the Vertex price: must lose to gemini/…
    "gemini/gemini-3.6-flash": {"input_cost_per_token": 7.5e-07, "output_cost_per_token": 3.75e-06, "cache_read_input_token_cost": 7.5e-08},
    "gemini/gemini-4-flash": {"input_cost_per_token": 1e-06, "output_cost_per_token": 5e-06},
    "grok-4.3": {"input_cost_per_token": "2e-06", "output_cost_per_token": "1e-05"},
    "broken-no-output": {"input_cost_per_token": 1e-06},
    "broken-negative": {"input_cost_per_token": -1, "output_cost_per_token": 1e-06},
    "broken-text": {"input_cost_per_token": "free", "output_cost_per_token": "free"},
    "not-an-entry": 5,
}
OPENROUTER = {"data": [
    {"id": "openai/gpt-5.5", "pricing": {"prompt": "0.000005", "completion": "0.00003", "input_cache_read": "0.0000005", "input_cache_write": "0"}},
    {"id": "google/gemini-3.6-flash", "pricing": {"prompt": "0.00000075", "completion": "0.00000375"}},
    {"id": "openrouter/auto", "pricing": {"prompt": "-1", "completion": "-1"}},
    {"id": "x/no-pricing"},
]}


def fetcher(*responses):
    """A mock transport: each call takes the next response ((status, body) or an exception)."""
    calls = []
    queue = list(responses)

    def fetch(url, timeout, max_bytes):
        calls.append((url, timeout, max_bytes))
        response = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(response, Exception):
            raise response
        return response

    fetch.calls = calls
    return fetch


def ok(payload):
    return 200, json.dumps(payload).encode("utf-8")


class Base(unittest.TestCase):
    def setUp(self):
        price_list._PREVIEWS.clear()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.database_path)
        self.project_id = self.storage.create_project({"title": "Fool me twice", "status": "translation"})["projectId"]
        self.storage.save_book_structure(
            self.project_id, "book.epub", "application/epub+zip", b"book",
            {"chapters": [{"title": "CHAPTER 38", "elements": [{"type": "paragraph", "text": "Secret book text."}]}]},
        )
        self.chapter_id = self.storage.get_book_structure(self.project_id)["chapters"][0]["chapterId"]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def service(self, *responses, clock=None):
        kwargs = {"clock": clock} if clock else {}
        return PriceListService(self.storage, fetcher(*responses), **kwargs)

    def sql(self, statement, *params):
        with sqlite3.connect(self.database_path) as connection:
            return connection.execute(statement, params).fetchall()

    def usage(self, created_at, engine="claude", model="claude-sonnet-5-5", kind="translate", project_id=None, **tokens):
        self.storage.record_translation_usage(project_id or self.project_id, self.chapter_id, engine, model, kind,
                                              {"input_tokens": tokens.get("input", 1000), "output_tokens": tokens.get("output", 100),
                                               "cache_read_input_tokens": tokens.get("cache_read", 0), "cache_creation_input_tokens": tokens.get("cache_write", 0)})
        self.sql("UPDATE translation_usage SET created_at = ? WHERE id = (SELECT MAX(id) FROM translation_usage)", created_at)


# ---- 0. a row without prices never shadows the undated model ---------------------------------


class ShadowingTests(Base):
    def test_a_priceless_dated_row_does_not_hide_the_undated_model(self):
        prices = {
            "gpt-5.5": {"inputPerMTok": 5, "outputPerMTok": 30, "cacheReadPerMTok": None, "cacheWritePerMTok": None},
            "gpt-5.5-2026-04-23": {"inputPerMTok": None, "outputPerMTok": None, "cacheReadPerMTok": None, "cacheWritePerMTok": None},
        }
        self.assertIs(prices["gpt-5.5"], find_price("gpt-5.5-2026-04-23", prices))
        self.assertIs(prices["gpt-5.5"], find_price("gpt-5.5", prices))
        self.assertIsNone(find_price("gpt-5.5-2026-04-23", {"gpt-5.5-2026-04-23": prices["gpt-5.5-2026-04-23"]}))

    def test_a_dated_row_with_its_own_price_still_wins(self):
        prices = {"gpt-5.5": {"inputPerMTok": 5}, "gpt-5.5-2026-04-23": {"inputPerMTok": 6}}
        self.assertEqual(6, find_price("gpt-5.5-2026-04-23", prices)["inputPerMTok"])

    def test_clearing_all_four_prices_deletes_the_row_and_no_empty_row_is_created(self):
        self.storage.save_model_prices([
            {"model": "gpt-5.5-2026-04-23", "inputPerMTok": None, "outputPerMTok": None},  # never existed: not created
            {"model": "gpt-5.5", "inputPerMTok": None, "outputPerMTok": None, "cacheReadPerMTok": None, "cacheWritePerMTok": None},
        ])
        prices = self.storage.list_model_prices()
        self.assertNotIn("gpt-5.5-2026-04-23", prices)
        self.assertNotIn("gpt-5.5", prices)
        self.assertEqual(2, len(prices))

    def test_the_migration_drops_priceless_rows_left_by_an_older_version(self):
        self.sql("INSERT INTO model_prices(model, updated_at, source) VALUES ('gpt-5.5-2026-04-23', 'x', 'manual')")
        Storage(self.database_path)
        self.assertEqual([], self.sql("SELECT model FROM model_prices WHERE model = 'gpt-5.5-2026-04-23'"))
        self.assertEqual(3, len(self.storage.list_model_prices()))


# ---- the table: source, deletion, restore -----------------------------------------------------


class PriceTableTests(Base):
    def test_seeded_rows_have_source_seed(self):
        prices = self.storage.list_model_prices()
        self.assertEqual({"seed"}, {item["source"] for item in prices.values()})

    def test_editing_makes_a_row_manual_but_saving_it_unchanged_does_not(self):
        before = self.storage.list_model_prices()["gpt-5.5"]
        self.storage.save_model_prices([{**before}])  # the UI sends every row on save
        self.assertEqual(("seed", before["updatedAt"]), tuple(self.storage.list_model_prices()["gpt-5.5"][key] for key in ("source", "updatedAt")))
        self.storage.save_model_prices([{**before, "inputPerMTok": 6}])
        edited = self.storage.list_model_prices()["gpt-5.5"]
        self.assertEqual(("manual", 6), (edited["source"], edited["inputPerMTok"]))

    def test_a_deleted_initial_model_stays_deleted_across_restarts_until_restored(self):
        self.storage.save_model_prices([{"model": "gemini-3.6-flash"}])
        for _ in range(2):
            self.storage = Storage(self.database_path)
        self.assertNotIn("gemini-3.6-flash", self.storage.list_model_prices())
        self.assertEqual(["gemini-3.6-flash"], self.storage.restore_default_prices())
        restored = self.storage.list_model_prices()["gemini-3.6-flash"]
        self.assertEqual(("seed", 1.5, 7.5), (restored["source"], restored["inputPerMTok"], restored["outputPerMTok"]))
        self.assertEqual([], self.storage.restore_default_prices())  # idempotent

    def test_restore_defaults_touches_neither_manual_nor_list_rows(self):
        self.storage.save_model_prices([{"model": "gpt-5.5", "inputPerMTok": 9, "outputPerMTok": 9}, {"model": "claude-sonnet-5-5"}])
        self.storage.apply_list_prices({"gemini-3.6-flash": {"inputPerMTok": 0.75, "outputPerMTok": 3.75}}, False)
        restored = self.storage.restore_default_prices()
        prices = self.storage.list_model_prices()
        self.assertEqual(["claude-sonnet-5-5"], restored)
        self.assertEqual(("manual", 9), (prices["gpt-5.5"]["source"], prices["gpt-5.5"]["inputPerMTok"]))
        self.assertEqual(("list", 0.75), (prices["gemini-3.6-flash"]["source"], prices["gemini-3.6-flash"]["inputPerMTok"]))
        self.assertEqual("seed", prices["claude-sonnet-5-5"]["source"])

    def test_a_table_without_the_source_column_is_upgraded_once(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript("""
                DROP TABLE model_prices;
                CREATE TABLE model_prices (model TEXT PRIMARY KEY, input_per_mtok REAL, output_per_mtok REAL,
                    cache_read_per_mtok REAL, cache_write_per_mtok REAL, updated_at TEXT NOT NULL);
                INSERT INTO model_prices VALUES ('gpt-5.5', 5, 30, NULL, NULL, 'old');
                INSERT INTO model_prices VALUES ('claude-sonnet-5-5', 2, 10, 0.5, 2.5, 'old');
                INSERT INTO model_prices VALUES ('custom', 1, 2, NULL, NULL, 'old');
                DELETE FROM app_settings;
            """)
        for _ in range(3):
            self.storage = Storage(self.database_path)
        prices = self.storage.list_model_prices()
        self.assertEqual("seed", prices["gpt-5.5"]["source"])        # still the initial value
        self.assertEqual("manual", prices["claude-sonnet-5-5"]["source"])  # cache price was edited
        self.assertEqual(0.5, prices["claude-sonnet-5-5"]["cacheReadPerMTok"])
        self.assertEqual("manual", prices["custom"]["source"])
        self.assertEqual("seed", prices["gemini-3.6-flash"]["source"])  # the missing initial model is seeded
        self.assertEqual(4, len(prices))


# ---- parsing the lists ------------------------------------------------------------------------


class ParsingTests(unittest.TestCase):
    def test_litellm_per_token_becomes_usd_per_million(self):
        catalog = parse_litellm(LITELLM)
        self.assertEqual({"inputPerMTok": 5.0, "outputPerMTok": 30.0, "cacheReadPerMTok": 0.5, "cacheWritePerMTok": None}, catalog["gpt-5.5"])
        self.assertEqual((2.0, 10.0, 0.1, 2.5), tuple(catalog["claude-sonnet-5-5"][key] for key in
                         ("inputPerMTok", "outputPerMTok", "cacheReadPerMTok", "cacheWritePerMTok")))
        self.assertEqual((0.75, 3.75, 0.075), tuple(catalog["gemini/gemini-3.6-flash"][key] for key in ("inputPerMTok", "outputPerMTok", "cacheReadPerMTok")))
        self.assertEqual((2.0, 10.0), (catalog["grok-4.3"]["inputPerMTok"], catalog["grok-4.3"]["outputPerMTok"]))  # numeric strings

    def test_placeholders_and_broken_entries_are_skipped(self):
        catalog = parse_litellm(LITELLM)
        for key in ("sample_spec", "broken-no-output", "broken-negative", "broken-text", "not-an-entry"):
            self.assertNotIn(key, catalog)

    def test_unexpected_formats_are_errors(self):
        for payload in ([], "x", {}, {"a": {"input_cost_per_token": None}}):
            with self.subTest(payload=payload), self.assertRaises(PriceListError):
                parse_litellm(payload)
        for payload in ({}, {"data": "x"}, {"data": []}, {"data": [{"id": "a", "pricing": {"prompt": "-1", "completion": "-1"}}]}):
            with self.subTest(payload=payload), self.assertRaises(PriceListError):
                parse_openrouter(payload)

    def test_openrouter_prices(self):
        catalog = parse_openrouter(OPENROUTER)
        self.assertEqual({"openai/gpt-5.5", "google/gemini-3.6-flash"}, set(catalog))
        self.assertEqual((5.0, 30.0, 0.5, 0.0), tuple(catalog["openai/gpt-5.5"][key] for key in
                         ("inputPerMTok", "outputPerMTok", "cacheReadPerMTok", "cacheWritePerMTok")))


class MatchingTests(unittest.TestCase):
    CATALOG = parse_litellm(LITELLM)

    def test_exact_names_and_provider_prefixes_only(self):
        self.assertEqual("gpt-5.5", match_model("gpt-5.5", "openai", self.CATALOG)[0])
        self.assertEqual("claude-sonnet-5-5", match_model("claude-sonnet-5-5", "claude", self.CATALOG)[0])
        self.assertEqual("gemini/gemini-4-flash", match_model("gemini-4-flash", "gemini", self.CATALOG)[0])
        self.assertEqual("gemini/gemini-4-flash", match_model("models/gemini-4-flash", None, self.CATALOG)[0])
        openrouter = parse_openrouter(OPENROUTER)
        self.assertEqual("openai/gpt-5.5", match_model("gpt-5.5", "openai", openrouter)[0])

    def test_the_gemini_api_price_wins_over_the_bare_vertex_one(self):
        key, prices = match_model("gemini-3.6-flash", "gemini", self.CATALOG)
        self.assertEqual(("gemini/gemini-3.6-flash", 0.75), (key, prices["inputPerMTok"]))

    def test_nothing_is_guessed_from_a_prefix(self):
        for model in ("gpt-5.5-2026-04-23", "gpt-5", "gpt-5.5x", "gpt", "claude-sonnet", "gemini-3.6", "gemini-3.6-flash-lite"):
            with self.subTest(model=model):
                self.assertIsNone(match_model(model, infer_engine(model), self.CATALOG))
        self.assertEqual("gpt-5.5-pro", match_model("gpt-5.5-pro", "openai", self.CATALOG)[0])  # only its own entry
        self.assertEqual("gpt-5.5-mini", match_model("gpt-5.5-mini", "openai", self.CATALOG)[0])


# ---- the preview ------------------------------------------------------------------------------


class PreviewTests(Base):
    def item(self, preview, model):
        return next(item for item in preview["items"] if item["model"] == model)

    def test_preview_compares_every_table_model_and_names_the_matched_key_without_writing(self):
        before = self.storage.list_model_prices()
        preview = self.service(ok(LITELLM)).preview()
        self.assertEqual(before, self.storage.list_model_prices())
        self.assertEqual(None, self.storage.get_setting("prices_updated_at"))
        self.assertEqual({"litellm", False, LITELLM_URL}, {preview["source"]["id"], preview["source"]["fallback"], preview["source"]["url"]})
        gemini = self.item(preview, "gemini-3.6-flash")
        self.assertEqual(("changed", "gemini/gemini-3.6-flash", "seed"), (gemini["status"], gemini["matchedKey"], gemini["current"]["source"]))
        self.assertEqual((1.5, 7.5), (gemini["current"]["inputPerMTok"], gemini["current"]["outputPerMTok"]))
        self.assertEqual((0.75, 3.75, 0.075), tuple(gemini["proposed"][key] for key in ("inputPerMTok", "outputPerMTok", "cacheReadPerMTok")))
        gpt = self.item(preview, "gpt-5.5")  # the list adds a cache-read price the seed does not have
        self.assertEqual(("changed", "gpt-5.5", None, 0.5), (gpt["status"], gpt["matchedKey"], gpt["current"]["cacheReadPerMTok"], gpt["proposed"]["cacheReadPerMTok"]))

    def test_cache_prices_the_list_lacks_are_kept_not_blanked(self):
        listed = {"gpt-5.5": {"input_cost_per_token": 5e-06, "output_cost_per_token": 3e-05}}
        self.storage.save_model_prices([{"model": "gpt-5.5", "inputPerMTok": 5, "outputPerMTok": 30, "cacheReadPerMTok": 0.5}])
        preview = self.service(ok(listed)).preview()
        self.assertEqual("same", self.item(preview, "gpt-5.5")["status"])
        self.assertEqual(0.5, self.item(preview, "gpt-5.5")["proposed"]["cacheReadPerMTok"])

    def test_models_without_a_match_are_shown_as_not_found(self):
        self.storage.save_model_prices([{"model": "my-local-model", "inputPerMTok": 1, "outputPerMTok": 2}])
        item = self.item(self.service(ok(LITELLM)).preview(), "my-local-model")
        self.assertEqual(("not_found", None, False), (item["status"], item["matchedKey"], item["defaultSelected"]))

    def test_unpriced_models_from_usage_are_included_but_priced_dated_ones_are_not(self):
        self.usage("2026-05-01T10:00:00+00:00", engine="gemini", model="gemini-4-flash")
        self.usage("2026-05-01T10:00:00+00:00", engine="openai", model="gpt-5.5-2026-04-23")  # priced through gpt-5.5
        self.usage("2026-05-01T10:00:00+00:00", engine="openai", model="gpt-5.5-mini")
        preview = self.service(ok(LITELLM)).preview()
        models = {item["model"] for item in preview["items"]}
        self.assertIn("gemini-4-flash", models)
        self.assertIn("gpt-5.5-mini", models)
        self.assertNotIn("gpt-5.5-2026-04-23", models)
        new = self.item(preview, "gemini-4-flash")
        self.assertEqual(("new", "gemini/gemini-4-flash", None, True), (new["status"], new["matchedKey"], new["current"], new["defaultSelected"]))
        self.assertEqual("gpt-5.5-mini", self.item(preview, "gpt-5.5-mini")["matchedKey"])  # not gpt-5.5

    def test_a_price_more_than_twice_off_is_flagged_and_not_selected_by_default(self):
        self.storage.save_model_prices([{"model": "gpt-5.5", "inputPerMTok": 1, "outputPerMTok": 30}])  # list says 5: 5x
        self.storage.apply_list_prices({"claude-sonnet-5-5": {"inputPerMTok": 2, "outputPerMTok": 10}}, False)
        preview = self.service(ok(LITELLM)).preview()
        gpt = self.item(preview, "gpt-5.5")
        self.assertEqual((True, False), (gpt["suspicious"], gpt["defaultSelected"]))
        # exactly twice (gemini 1.5 -> 0.75) is not "more than twice"; cache 0.20 -> 0.10 likewise
        gemini = self.item(preview, "gemini-3.6-flash")
        self.assertEqual((False, True), (gemini["suspicious"], gemini["defaultSelected"]))

    def test_manual_rows_are_not_selected_by_default(self):
        self.storage.save_model_prices([{"model": "claude-sonnet-5-5", "inputPerMTok": 2, "outputPerMTok": 10, "cacheReadPerMTok": 0.2}])
        item = self.item(self.service(ok(LITELLM)).preview(), "claude-sonnet-5-5")
        self.assertEqual(("changed", True, False), (item["status"], item["protectedManual"], item["defaultSelected"]))


class FetchingTests(Base):
    def test_a_failed_first_source_falls_back_to_openrouter(self):
        for first in ((500, b""), (200, b"not json"), (200, b"[]"), PriceListError("down"), (200, b"x" * (price_list.MAX_RESPONSE_BYTES + 1))):
            with self.subTest(first=str(first)[:40]):
                service = self.service(first, ok(OPENROUTER))
                preview = service.preview()
                self.assertEqual(("openrouter", True), (preview["source"]["id"], preview["source"]["fallback"]))
                self.assertEqual([LITELLM_URL, OPENROUTER_URL], [call[0] for call in service._fetcher.calls])
                self.assertEqual("openai/gpt-5.5", next(item for item in preview["items"] if item["model"] == "gpt-5.5")["matchedKey"])

    def test_when_both_fail_there_is_a_readable_error_and_nothing_changes(self):
        before = self.storage.list_model_prices()
        with self.assertRaises(PriceListError) as raised:
            self.service((503, b""), PriceListError("Не вдалося з’єднатися")).preview()
        self.assertEqual(502, raised.exception.http_status)
        self.assertEqual(before, self.storage.list_model_prices())

    def test_only_the_two_fixed_urls_with_a_timeout_and_a_size_cap_are_used(self):
        service = self.service(ok(LITELLM))
        service.preview()
        (url, timeout, max_bytes), = service._fetcher.calls
        self.assertEqual((LITELLM_URL, price_list.FETCH_TIMEOUT_SECONDS, price_list.MAX_RESPONSE_BYTES), (url, timeout, max_bytes))
        self.assertLessEqual(timeout, 30)
        self.assertEqual({LITELLM_URL, OPENROUTER_URL}, set(price_list.ALLOWED_URLS))

    def test_default_fetch_refuses_other_urls_and_never_follows_redirects(self):
        with self.assertRaises(PriceListError):
            default_fetch("https://example.com/prices.json", 5, 100)

        class Opener:
            def __init__(self, error=None, body=b""):
                self.error, self.body = error, body

            def open(self, request, timeout):
                if self.error:
                    raise self.error
                body = self.body

                class Response:
                    status = 200

                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        return False

                    def read(self, count):
                        return body[:count]

                return Response()

        redirect = HTTPError(LITELLM_URL, 302, "Found", {}, None)
        with patch.object(price_list, "build_opener", return_value=Opener(error=redirect)):
            self.assertEqual((302, b""), default_fetch(LITELLM_URL, 5, 100))
        with patch.object(price_list, "build_opener", return_value=Opener(body=b"x" * 500)):
            with self.assertRaises(PriceListError):
                default_fetch(LITELLM_URL, 5, 100)
        with patch.object(price_list, "build_opener", return_value=Opener(body=b"{}")):
            self.assertEqual((200, b"{}"), default_fetch(LITELLM_URL, 5, 100))
        sent = []

        class Spy(Opener):
            def open(self, request, timeout):
                sent.append(dict(request.header_items()))
                return super().open(request, timeout)

        with patch.object(price_list, "build_opener", return_value=Spy(body=b"{}")):
            default_fetch(LITELLM_URL, 5, 100)
        self.assertEqual({"Accept", "User-agent"}, set(sent[0]))  # no keys, cookies or authorization


# ---- applying --------------------------------------------------------------------------------


class ApplyTests(Base):
    def test_only_the_confirmed_models_are_written_and_marked_as_list(self):
        self.usage("2026-05-01T10:00:00+00:00", engine="gemini", model="gemini-4-flash")
        service = self.service(ok(LITELLM))
        preview = service.preview()
        result = service.apply(preview["previewId"], ["gemini-3.6-flash", "gemini-4-flash"], False)
        self.assertEqual({"gemini-3.6-flash", "gemini-4-flash"}, set(result["applied"]))
        prices = self.storage.list_model_prices()
        self.assertEqual(("list", 0.75, 3.75, 0.075), tuple(prices["gemini-3.6-flash"][key] for key in
                         ("source", "inputPerMTok", "outputPerMTok", "cacheReadPerMTok")))
        self.assertEqual(("list", 1.0), (prices["gemini-4-flash"]["source"], prices["gemini-4-flash"]["inputPerMTok"]))
        self.assertEqual("seed", prices["gpt-5.5"]["source"])  # not selected: untouched
        self.assertEqual("seed", prices["claude-sonnet-5-5"]["source"])
        self.assertEqual(5.0, prices["gpt-5.5"]["inputPerMTok"])
        self.assertIsNotNone(self.storage.get_setting("prices_updated_at"))
        self.assertEqual("litellm", json.loads(self.storage.get_setting("prices_updated_source"))["id"])

    def test_manual_prices_survive_unless_the_overwrite_box_is_ticked(self):
        self.storage.save_model_prices([{"model": "gemini-3.6-flash", "inputPerMTok": 2, "outputPerMTok": 9}])
        service = self.service(ok(LITELLM))
        preview = service.preview()
        skipped = service.apply(preview["previewId"], ["gemini-3.6-flash"], False)
        self.assertEqual((["gemini-3.6-flash"], []), (skipped["skippedManual"], skipped["applied"]))
        self.assertEqual(("manual", 2), tuple(self.storage.list_model_prices()["gemini-3.6-flash"][k] for k in ("source", "inputPerMTok")))
        self.assertIsNone(self.storage.get_setting("prices_updated_at"))  # nothing was applied
        forced = service.apply(preview["previewId"], ["gemini-3.6-flash"], True)
        self.assertEqual(["gemini-3.6-flash"], forced["applied"])
        self.assertEqual(("list", 0.75), tuple(self.storage.list_model_prices()["gemini-3.6-flash"][k] for k in ("source", "inputPerMTok")))

    def test_an_edit_made_after_the_preview_is_still_protected(self):
        service = self.service(ok(LITELLM))
        preview = service.preview()
        self.storage.save_model_prices([{"model": "gemini-3.6-flash", "inputPerMTok": 2, "outputPerMTok": 9}])  # edited meanwhile
        self.assertEqual(["gemini-3.6-flash"], service.apply(preview["previewId"], ["gemini-3.6-flash"], False)["skippedManual"])

    def test_apply_needs_a_live_preview_and_never_takes_prices_from_the_client(self):
        now = [1000.0]
        service = self.service(ok(LITELLM), clock=lambda: now[0])
        preview = service.preview()
        now[0] += price_list.PREVIEW_TTL_SECONDS + 1
        with self.assertRaises(PriceListError) as raised:
            service.apply(preview["previewId"], ["gemini-3.6-flash"], False)
        self.assertEqual((409, "price_preview_expired"), (raised.exception.http_status, raised.exception.code))
        for bad in ("unknown", None, 5):
            with self.assertRaises(PriceListError):
                service.apply(bad, ["gemini-3.6-flash"], False)
        with self.assertRaises(PriceListError):
            service.apply(preview["previewId"], "gemini-3.6-flash", False)
        # a model that is not in the preview cannot be written, whatever the client asks
        fresh = self.service(ok(LITELLM))
        preview = fresh.preview()
        result = fresh.apply(preview["previewId"], ["not-in-the-preview", "gpt-5.5"], False)
        self.assertEqual((["not-in-the-preview"], ["gpt-5.5"]), (result["unknown"], result["applied"]))
        self.assertNotIn("not-in-the-preview", self.storage.list_model_prices())

    def test_costs_follow_the_applied_prices(self):
        self.usage("2026-05-01T10:00:00+00:00", engine="gemini", model="gemini-3.6-flash", input=1_000_000, output=0)
        report = lambda: daily_report(self.storage.list_translation_usage_all(), self.storage.list_model_prices(), KYIV, 90, date(2026, 5, 2))["total"]["costUsd"]
        self.assertAlmostEqual(1.5, report())
        service = self.service(ok(LITELLM))
        service.apply(service.preview()["previewId"], ["gemini-3.6-flash"], False)
        self.assertAlmostEqual(0.75, report())


class PriceApiTests(Base):
    class Handler:
        def __init__(self, payload=None):
            self.payload = payload

        def read_json(self):
            return self.payload

    def api(self, method, path, payload=None, responses=(ok(LITELLM),)):
        with patch.object(server, "storage", self.storage), patch.object(server, "price_list_fetcher", fetcher(*responses)):
            return server.WorkbenchHandler.handle_api(self.Handler(payload), method, path)

    def test_refresh_and_apply_through_the_api(self):
        status, preview = self.api("POST", "/api/model-prices/refresh", {})
        self.assertEqual(200, status)
        status, body = self.api("POST", "/api/model-prices/apply", {"previewId": preview["previewId"], "models": ["gemini-3.6-flash"]})
        self.assertEqual(200, status)
        self.assertEqual(["gemini-3.6-flash"], body["applied"])
        self.assertEqual("litellm", body["source"]["id"])
        self.assertTrue(body["updatedAt"])
        self.assertEqual("list", next(item for item in body["prices"] if item["model"] == "gemini-3.6-flash")["source"])
        self.assertEqual("litellm", self.api("GET", "/api/model-prices")[1]["source"]["id"])

    def test_overwrite_manual_must_be_exactly_true(self):
        self.storage.save_model_prices([{"model": "gemini-3.6-flash", "inputPerMTok": 2, "outputPerMTok": 9}])
        _status, preview = self.api("POST", "/api/model-prices/refresh", {})
        for flag in ("true", 1, "yes", None):
            body = self.api("POST", "/api/model-prices/apply", {"previewId": preview["previewId"], "models": ["gemini-3.6-flash"], "overwriteManual": flag})[1]
            self.assertEqual(["gemini-3.6-flash"], body["skippedManual"])
        body = self.api("POST", "/api/model-prices/apply", {"previewId": preview["previewId"], "models": ["gemini-3.6-flash"], "overwriteManual": True})[1]
        self.assertEqual(["gemini-3.6-flash"], body["applied"])

    def test_errors_are_raised_for_the_handler_to_turn_into_http_errors(self):
        with self.assertRaises(PriceListError):
            self.api("POST", "/api/model-prices/refresh", {}, responses=((500, b""),))
        with self.assertRaises(PriceListError) as raised:
            self.api("POST", "/api/model-prices/apply", {"previewId": "nope", "models": []})
        self.assertEqual(409, raised.exception.http_status)

    def test_restore_defaults_endpoint(self):
        self.api("PUT", "/api/model-prices", {"prices": [{"model": "gpt-5.5"}]})
        self.assertNotIn("gpt-5.5", {item["model"] for item in self.api("GET", "/api/model-prices")[1]["prices"]})
        status, body = self.api("POST", "/api/model-prices/restore-defaults", {})
        self.assertEqual((200, ["gpt-5.5"]), (status, body["restored"]))
        self.assertIn("gpt-5.5", {item["model"] for item in body["prices"]})


# ---- days in a time zone ----------------------------------------------------------------------


def day_of(rows_at, zone=KYIV, today=date(2026, 12, 31), days=90):
    rows = [{"createdAt": moment, "engine": "claude", "model": "claude-sonnet-5-5", "kind": "translate", "inputTokens": 1000,
             "outputTokens": 100, "cacheReadTokens": 0, "cacheWriteTokens": 0} for moment in rows_at]
    report = daily_report(rows, {"claude-sonnet-5-5": {"inputPerMTok": 2, "outputPerMTok": 10}}, zone, days, today)
    return {entry["date"]: entry["calls"] for entry in report["rows"] if entry["calls"]}


class TimezoneTests(unittest.TestCase):
    def test_the_midnight_boundary_in_summer_time(self):
        # Kyiv is UTC+3 in summer: 21:00 UTC is midnight
        self.assertEqual({"2026-06-30": 1, "2026-07-01": 1}, day_of(["2026-06-30T20:59:59+00:00", "2026-06-30T21:00:00+00:00"], today=date(2026, 7, 10)))

    def test_the_midnight_boundary_in_winter_time(self):
        self.assertEqual({"2026-12-31": 1, "2027-01-01": 1},
                         day_of(["2026-12-31T21:59:59+00:00", "2026-12-31T22:00:00+00:00"], today=date(2027, 1, 5)))

    def test_the_day_the_clocks_go_forward_has_23_hours(self):
        # 29 March 2026: 03:00 -> 04:00 at 01:00 UTC; midnight is 22:00 UTC on the 28th (EET) and 21:00 UTC on the 29th (EEST)
        self.assertEqual({"2026-03-28": 1, "2026-03-29": 2, "2026-03-30": 1},
                         day_of(["2026-03-28T21:59:59+00:00", "2026-03-28T22:00:00+00:00", "2026-03-29T20:59:59+00:00", "2026-03-29T21:00:00+00:00"],
                                today=date(2026, 4, 2)))
        self.assertEqual(
            (local_day_start_utc(date(2026, 3, 30), KYIV) - local_day_start_utc(date(2026, 3, 29), KYIV)).total_seconds(), 23 * 3600)

    def test_the_day_the_clocks_go_back_has_25_hours(self):
        self.assertEqual({"2026-10-24": 1, "2026-10-25": 2, "2026-10-26": 1},
                         day_of(["2026-10-24T20:59:59+00:00", "2026-10-24T21:00:00+00:00", "2026-10-25T21:59:59+00:00", "2026-10-25T22:00:00+00:00"],
                                today=date(2026, 10, 30)))
        self.assertEqual(
            (local_day_start_utc(date(2026, 10, 26), KYIV) - local_day_start_utc(date(2026, 10, 25), KYIV)).total_seconds(), 25 * 3600)

    def test_the_stored_time_stays_utc_and_a_different_zone_groups_differently(self):
        moments = ["2026-06-30T21:30:00+00:00"]
        self.assertEqual({"2026-07-01": 1}, day_of(moments, KYIV, today=date(2026, 7, 5)))
        self.assertEqual({"2026-06-30": 1}, day_of(moments, ZoneInfo("UTC"), today=date(2026, 7, 5)))
        self.assertEqual({"2026-06-30": 1}, day_of(moments, ZoneInfo("America/New_York"), today=date(2026, 7, 5)))
        self.assertEqual(date(2026, 7, 1), local_date("2026-06-30T21:30:00", KYIV))  # a naive timestamp is UTC

    def test_zone_names_are_validated_and_fall_back_to_kyiv(self):
        self.assertIsNotNone(resolve_timezone("Europe/Kyiv"))
        self.assertIsNotNone(resolve_timezone("UTC"))
        for bad in ("Mars/Phobos", "", None, 5, "../etc/passwd", "Europe/Kyiv/../../x", "x" * 100, "Europe Kyiv", "/etc/localtime"):
            with self.subTest(bad=bad):
                self.assertIsNone(resolve_timezone(bad))
                self.assertEqual("Europe/Kyiv", timezone_or_default(bad).key)

    def test_empty_days_are_kept_and_the_range_is_exact(self):
        report = daily_report([], {}, KYIV, 7, date(2026, 3, 31))
        self.assertEqual(["2026-03-25", "2026-03-26", "2026-03-27", "2026-03-28", "2026-03-29", "2026-03-30", "2026-03-31"], [row["date"] for row in report["rows"]])
        self.assertEqual((0, 0.0, "Europe/Kyiv"), (report["total"]["calls"], report["total"]["costUsd"], report["timezone"]))
        self.assertEqual(90, len(daily_report([], {}, KYIV, 90, date(2026, 3, 31))["rows"]))

    def test_rows_outside_the_range_are_not_counted(self):
        self.assertEqual({"2026-04-01": 1}, day_of(["2026-03-01T10:00:00+00:00", "2026-04-01T10:00:00+00:00", "2026-04-09T10:00:00+00:00"],
                                                    today=date(2026, 4, 7), days=7))


class DailyReportTests(unittest.TestCase):
    PRICES = {"claude-sonnet-5-5": {"inputPerMTok": 2, "outputPerMTok": 10, "cacheReadPerMTok": 0.2, "cacheWritePerMTok": 2.5}}

    def row(self, at, engine="claude", model="claude-sonnet-5-5", kind="translate", **tokens):
        return {"createdAt": at, "engine": engine, "model": model, "kind": kind, "inputTokens": tokens.get("input", 1_000_000),
                "outputTokens": tokens.get("output", 0), "cacheReadTokens": tokens.get("cache_read", 0), "cacheWriteTokens": tokens.get("cache_write", 0)}

    def test_totals_tokens_and_breakdowns_per_day_and_range(self):
        rows = [
            self.row("2026-05-01T10:00:00+00:00", output=100_000, cache_read=500_000),
            self.row("2026-05-01T11:00:00+00:00", kind="retry", input=500_000),
            self.row("2026-05-02T10:00:00+00:00", kind="qa", engine="claude", cache_write=100_000, input=0),
        ]
        report = daily_report(rows, self.PRICES, KYIV, 7, date(2026, 5, 3))
        first = next(entry for entry in report["rows"] if entry["date"] == "2026-05-01")
        self.assertEqual((2, 1_500_000, 100_000, 500_000), (first["calls"], first["inputTokens"], first["outputTokens"], first["cacheReadTokens"]))
        self.assertAlmostEqual(2 + 1 + 0.1 * 1 + 1.0, first["costUsd"])  # 1M in + 0.5M in + 0.1M out*10/1M... computed below
        self.assertEqual({"translate", "retry"}, {item["kind"] for item in first["byKind"]})
        self.assertEqual(["claude"], [item["engine"] for item in first["byEngine"]])
        self.assertEqual({"translate": 1, "retry": 1, "qa": 1}, {item["kind"]: item["calls"] for item in report["byKind"]})
        self.assertEqual(3, report["total"]["calls"])

    def test_calls_without_a_price_are_counted_and_make_the_sum_incomplete(self):
        rows = [self.row("2026-05-01T10:00:00+00:00"), self.row("2026-05-01T11:00:00+00:00", model="mystery"), self.row("2026-05-02T10:00:00+00:00", model="mystery")]
        report = daily_report(rows, self.PRICES, KYIV, 7, date(2026, 5, 3))
        first = next(entry for entry in report["rows"] if entry["date"] == "2026-05-01")
        second = next(entry for entry in report["rows"] if entry["date"] == "2026-05-02")
        third = next(entry for entry in report["rows"] if entry["date"] == "2026-05-03")
        self.assertEqual((1, True, 2.0, 2), (first["unpricedCalls"], first["incomplete"], first["costUsd"], first["calls"]))
        self.assertEqual((1, True, None), (second["unpricedCalls"], second["incomplete"], second["costUsd"]))  # nothing could be priced
        self.assertEqual((0, False), (third["unpricedCalls"], third["incomplete"]))
        self.assertEqual((2, True, ["mystery"]), (report["total"]["unpricedCalls"], report["total"]["incomplete"], report["unpricedModels"]))
        self.assertEqual(3, report["total"]["calls"])  # never dropped silently

    def test_a_dated_model_is_priced_through_its_undated_row_but_a_priceless_row_does_not_shadow_it(self):
        prices = {**self.PRICES, "claude-sonnet-5-5-20260101": {"inputPerMTok": None, "outputPerMTok": None}}
        report = daily_report([self.row("2026-05-01T10:00:00+00:00", model="claude-sonnet-5-5-20260101")], prices, KYIV, 7, date(2026, 5, 3))
        self.assertEqual((2.0, False), (report["total"]["costUsd"], report["total"]["incomplete"]))


class CsvTests(unittest.TestCase):
    def rows(self, text):
        return list(csv.reader(io.StringIO(text.lstrip("﻿"))))

    def test_one_line_per_day_project_engine_model_kind_with_a_header_and_no_book_text(self):
        records = [
            {"createdAt": "2026-06-30T21:30:00+00:00", "projectId": "p1", "engine": "claude", "model": "claude-sonnet-5-5", "kind": "translate",
             "inputTokens": 1_000_000, "outputTokens": 0, "cacheReadTokens": 0, "cacheWriteTokens": 0},
            {"createdAt": "2026-07-01T09:00:00+00:00", "projectId": "p1", "engine": "claude", "model": "claude-sonnet-5-5", "kind": "translate",
             "inputTokens": 500_000, "outputTokens": 0, "cacheReadTokens": 100_000, "cacheWriteTokens": 0},
            {"createdAt": "2026-07-01T09:00:00+00:00", "projectId": "p1", "engine": "openai", "model": "mystery", "kind": "qa",
             "inputTokens": 10, "outputTokens": 5, "cacheReadTokens": 0, "cacheWriteTokens": 0},
            {"createdAt": "2026-08-01T09:00:00+00:00", "projectId": "p1", "engine": "claude", "model": "claude-sonnet-5-5", "kind": "chat",
             "inputTokens": 1, "outputTokens": 1, "cacheReadTokens": 0, "cacheWriteTokens": 0},
        ]
        prices = {"claude-sonnet-5-5": {"inputPerMTok": 2, "outputPerMTok": 10, "cacheReadPerMTok": None}}
        text = usage_csv(records, prices, KYIV, date(2026, 7, 1), date(2026, 7, 31), {"p1": "Fool me twice"})
        self.assertTrue(text.startswith("﻿"))
        table = self.rows(text)
        self.assertEqual(["date", "project", "engine", "model", "kind", "calls", "input_tokens", "output_tokens",
                          "cache_read_tokens", "cache_write_tokens", "cost_usd", "cost_note"], table[0])
        self.assertEqual(2, len(table) - 1)  # 2026-06-30 21:30Z is July 1st in Kyiv and joins the next record; August is out of range
        first, second = table[1:]
        self.assertEqual(["2026-07-01", "Fool me twice", "claude", "claude-sonnet-5-5", "translate", "2", "1500000", "0", "100000", "0", "3.200000", "estimate"], first)
        self.assertEqual(["openai", "mystery", "qa", "1", "10", "5"], [second[2], second[3], second[4], second[5], second[6], second[7]])
        self.assertEqual(("", "no price"), (second[10], second[11]))  # not silently priced at zero
        self.assertNotIn("Secret", text)

    def test_text_cells_cannot_run_as_formulas(self):
        record = {"createdAt": "2026-07-01T09:00:00+00:00", "projectId": "p1", "engine": "claude", "model": "=1+1", "kind": "chat",
                  "inputTokens": 1, "outputTokens": 1, "cacheReadTokens": 0, "cacheWriteTokens": 0}
        for title in ("=HYPERLINK(\"http://x\")", "+1", "-1", "@SUM(1)", "\tx"):
            with self.subTest(title=title):
                row = self.rows(usage_csv([record], {}, KYIV, date(2026, 7, 1), date(2026, 7, 1), {"p1": title}))[1]
                self.assertEqual("'" + title, row[1])
                self.assertEqual("'=1+1", row[3])


class UsageApiTests(Base):
    class Handler:
        def __init__(self, payload=None):
            self.payload = payload

        def read_json(self):
            return self.payload

    def api(self, method, path, payload=None):
        handler = self.Handler(payload)
        handler.path = path  # the real server passes the path without the query string to handle_api
        with patch.object(server, "storage", self.storage):
            return server.WorkbenchHandler.handle_api(handler, method, path.split("?")[0])

    def now(self):
        return self.sql("SELECT strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now')")[0][0]

    def test_daily_endpoint_scopes_ranges_and_the_project_filter(self):
        other = self.storage.create_project({"title": "Other", "status": "translation"})["projectId"]
        self.storage.record_translation_usage(self.project_id, self.chapter_id, "claude", "claude-sonnet-5-5", "translate", {"input_tokens": 100, "output_tokens": 10})
        self.storage.record_translation_usage(other, None, "openai", "gpt-5.5", "chat", {"input_tokens": 50, "output_tokens": 5})
        status, everything = self.api("GET", "/api/usage/daily?days=7")
        self.assertEqual((200, 7, 2, None), (status, len(everything["rows"]), everything["total"]["calls"], everything["projectId"]))
        status, one = self.api("GET", f"/api/usage/daily?days=30&projectId={self.project_id}")
        self.assertEqual((200, 30, 1, self.project_id), (status, len(one["rows"]), one["total"]["calls"], one["projectId"]))
        self.assertEqual(["claude"], [item["engine"] for item in one["byEngine"]])
        self.assertEqual(90, len(self.api("GET", "/api/usage/daily?days=90")[1]["rows"]))
        for bad in ("days=8", "days=0", "days=x", "days=-7"):
            self.assertEqual(400, self.api("GET", f"/api/usage/daily?{bad}")[0])
        self.assertEqual(404, self.api("GET", "/api/usage/daily?days=7&projectId=nope")[0])
        self.assertNotIn("Secret book text", json.dumps(everything, ensure_ascii=False))

    def test_the_time_zone_setting_is_validated_and_changes_the_grouping_on_the_fly(self):
        self.assertEqual("Europe/Kyiv", self.api("GET", "/api/settings")[1]["timezone"])
        self.assertEqual(400, self.api("PUT", "/api/settings", {"timezone": "Mars/Phobos"})[0])
        self.assertEqual(400, self.api("PUT", "/api/settings", {})[0])
        self.assertEqual("Europe/Kyiv", self.api("GET", "/api/settings")[1]["timezone"])
        self.storage.record_translation_usage(self.project_id, None, "claude", "claude-sonnet-5-5", "chat", {"input_tokens": 1})
        stored = self.sql("SELECT created_at FROM translation_usage")[0][0]
        self.assertEqual("+00:00", stored[-6:])  # created_at stays UTC
        self.assertEqual(200, self.api("PUT", "/api/settings", {"timezone": "Pacific/Kiritimati"})[0])  # UTC+14
        report = self.api("GET", "/api/usage/daily?days=7")[1]
        self.assertEqual("Pacific/Kiritimati", report["timezone"])
        self.assertEqual(1, report["total"]["calls"])
        self.assertEqual(stored, self.sql("SELECT created_at FROM translation_usage")[0][0])  # nothing was rewritten

    def test_an_invalid_stored_zone_falls_back_to_kyiv_without_failing(self):
        self.sql("INSERT INTO app_settings(key, value) VALUES ('timezone', 'Mars/Phobos')")
        self.storage.record_translation_usage(self.project_id, None, "claude", "claude-sonnet-5-5", "chat", {"input_tokens": 1})
        self.assertEqual("Europe/Kyiv", self.api("GET", "/api/settings")[1]["timezone"])
        status, report = self.api("GET", "/api/usage/daily?days=7")
        self.assertEqual((200, "Europe/Kyiv", 1), (status, report["timezone"], report["total"]["calls"]))
        with patch.object(server, "storage", self.storage):
            status, _error, filename, content = server.usage_export({})
        self.assertEqual(200, status)

    def test_export_range_validation_and_content(self):
        self.storage.record_translation_usage(self.project_id, self.chapter_id, "claude", "claude-sonnet-5-5", "translate", {"input_tokens": 100, "output_tokens": 10})
        with patch.object(server, "storage", self.storage):
            status, _error, filename, content = server.usage_export({"from": ["2000-01-01"], "to": ["2100-01-01"]})
            self.assertEqual(400, status)  # more than a year
            self.assertEqual(400, server.usage_export({"from": ["2026-02-30"]})[0])
            self.assertEqual(400, server.usage_export({"from": ["2026-07-02"], "to": ["2026-07-01"]})[0])
            self.assertEqual(404, server.usage_export({"projectId": ["nope"]})[0])
            status, _error, filename, content = server.usage_export({})
        self.assertEqual(200, status)
        self.assertRegex(filename, r"^usage-\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}\.csv$")
        table = list(csv.reader(io.StringIO(content.lstrip("﻿"))))
        self.assertEqual(["Fool me twice", "claude", "claude-sonnet-5-5", "translate"], table[1][1:5])
        self.assertNotIn("Secret", content)


if __name__ == "__main__":
    unittest.main()
