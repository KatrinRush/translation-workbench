from email import policy
from email.parser import BytesParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import sys
from urllib.parse import unquote, urlparse
from urllib.parse import quote

import sqlite3

try:
    # Works when launched as `python -m backend.server` from the repo root.
    from .integrations.credentials import CredentialVault
    from .integrations.providers import ClaudeProvider, DeepLProvider, GeminiProvider, OpenAIProvider
    from .integrations.registry import ProviderRegistry
    from .integrations.service import IntegrationService, IntegrationServiceError
    from .parsers import parse_epub
    from .storage import Storage
    from .translations import TranslationService, TranslationServiceError
except ImportError:
    # Works when launched as `python server.py` from inside backend/.
    from integrations.credentials import CredentialVault
    from integrations.providers import ClaudeProvider, DeepLProvider, GeminiProvider, OpenAIProvider
    from integrations.registry import ProviderRegistry
    from integrations.service import IntegrationService, IntegrationServiceError
    from parsers import parse_epub
    from storage import Storage
    from translations import TranslationService, TranslationServiceError


HOST = os.environ.get("WORKBENCH_HOST", "127.0.0.1")
PORT = 8000
MAX_UPLOAD_SIZE = 50 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".epub"}
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
storage = Storage()
credential_vault = CredentialVault.from_environment()
provider_registry = ProviderRegistry([DeepLProvider(), OpenAIProvider(), GeminiProvider(), ClaudeProvider()])
integration_service = IntegrationService(
    storage,
    credential_vault,
    provider_registry,
)
translation_service = TranslationService(storage, credential_vault, provider_registry)


def parse_multipart(content_type, body):
    headers = (
        f"Content-Type: {content_type}\r\n"
        "MIME-Version: 1.0\r\n\r\n"
    ).encode("utf-8")
    message = BytesParser(policy=policy.default).parsebytes(headers + body)
    for part in message.iter_parts():
        if part.get_content_disposition() == "form-data" and part.get_param("name", header="content-disposition") == "file":
            filename = part.get_filename()
            payload = part.get_payload(decode=True)
            if filename and payload is not None:
                return filename, payload
    raise ValueError("Файл не було передано.")


def validate_project_ai_configuration(data, connections):
    ai_configuration = data.get("aiConfiguration")
    if ai_configuration is None:
        return None
    if not isinstance(ai_configuration, dict):
        return "AI configuration must be an object."
    connection_ids = []
    for key in ("translationConnectionId", "orchestrationConnectionId"):
        value = ai_configuration.get(key)
        if value is not None:
            connection_ids.append(value)
    for key in ("analysisConnectionIds", "qaConnectionIds"):
        values = ai_configuration.get(key, [])
        if not isinstance(values, list):
            return f"{key} must be a list."
        connection_ids.extend(values)
    if any(not isinstance(connection_id, str) or not connection_id.strip() for connection_id in connection_ids):
        return "AI connection IDs must be non-empty strings."
    existing_connection_ids = {connection["connectionId"] for connection in connections}
    if any(connection_id not in existing_connection_ids for connection_id in connection_ids):
        return "AI configuration references an unknown connection."
    return None


class WorkbenchHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def send_json(self, status, payload):
        if status == 204:
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def send_download(self, filename, content):
        ascii_filename = "".join(character if ord(character) < 128 and (character.isalnum() or character in "-_.") else "_" for character in filename)
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(filename)}')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def read_json(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0:
            raise ValueError("JSON body is required.")
        try:
            return json.loads(self.rfile.read(size).decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Invalid JSON body.") from error

    def handle_api(self, method, path):
        parts = [unquote(part) for part in path.split("/") if part]
        if parts == ["api", "integration-providers"] and method == "GET":
            return 200, integration_service.list_providers()
        if parts == ["api", "connections"]:
            if method == "GET":
                return 200, integration_service.list_connections()
            if method == "POST":
                return 201, integration_service.create_connection(self.read_json())
        if len(parts) == 3 and parts[:2] == ["api", "connections"]:
            connection_id = parts[2]
            if method == "GET":
                return 200, integration_service.get_connection(connection_id)
            if method in {"PUT", "PATCH"}:
                return 200, integration_service.update_connection(connection_id, self.read_json())
            if method == "DELETE":
                integration_service.delete_connection(connection_id)
                return 204, None
        if len(parts) == 4 and parts[:2] == ["api", "connections"]:
            connection_id = parts[2]
            if parts[3] == "test" and method == "POST":
                return 200, integration_service.test_connection(connection_id)
            if parts[3] == "status" and method == "GET":
                return 200, integration_service.get_status(connection_id)
        if parts == ["api", "authors"]:
            if method == "GET":
                return 200, storage.list_authors()
            if method == "POST":
                return 201, storage.create_author(self.read_json())
        if len(parts) == 3 and parts[:2] == ["api", "authors"]:
            author_id = parts[2]
            if method in {"PUT", "PATCH"}:
                author = storage.update_author(author_id, self.read_json())
                return (200, author) if author else (404, {"error": "Author not found."})
            if method == "DELETE":
                if not storage.delete_author(author_id):
                    return 404, {"error": "Author not found."}
                return 204, None
        if parts == ["api", "series"]:
            if method == "GET":
                return 200, storage.list_series()
            if method == "POST":
                return 201, storage.create_series(self.read_json())
        if len(parts) == 3 and parts[:2] == ["api", "series"]:
            series_id = parts[2]
            if method in {"PUT", "PATCH"}:
                series = storage.update_series(series_id, self.read_json())
                return (200, series) if series else (404, {"error": "Series not found."})
            if method == "DELETE":
                if not storage.delete_series(series_id):
                    return 404, {"error": "Series not found."}
                return 204, None
        if parts == ["api", "rules"]:
            if method == "GET":
                return 200, storage.list_rules()
            if method == "POST":
                return 201, storage.create_rule(self.read_json())
        if len(parts) == 3 and parts[:2] == ["api", "rules"]:
            rule_id = parts[2]
            if method in {"PUT", "PATCH"}:
                rule = storage.update_rule(rule_id, self.read_json())
                return (200, rule) if rule else (404, {"error": "Rule not found."})
            if method == "DELETE":
                if not storage.delete_rule(rule_id):
                    return 404, {"error": "Rule not found."}
                return 204, None
        if parts == ["api", "glossary"]:
            if method == "GET":
                return 200, storage.list_glossary()
            if method == "POST":
                return 201, storage.create_glossary_entry(self.read_json())
        if len(parts) == 3 and parts[:2] == ["api", "glossary"]:
            entry_id = parts[2]
            if method in {"PUT", "PATCH"}:
                entry = storage.update_glossary_entry(entry_id, self.read_json())
                return (200, entry) if entry else (404, {"error": "Glossary entry not found."})
            if method == "DELETE":
                if not storage.delete_glossary_entry(entry_id):
                    return 404, {"error": "Glossary entry not found."}
                return 204, None
        if len(parts) == 4 and parts[:2] == ["api", "series-author-contexts"]:
            series_id, author_id = parts[2], parts[3]
            if method == "GET":
                context = storage.get_series_author_context(series_id, author_id)
                return (200, context) if context else (404, {"error": "Context not found."})
            return 200, storage.upsert_series_author_context(series_id, author_id, self.read_json())
        if parts == ["api", "projects"]:
            if method == "GET":
                return 200, storage.list_projects()
            data = self.read_json()
            validation_error = validate_project_ai_configuration(data, storage.list_integration_connections())
            if validation_error:
                return 400, {"error": validation_error}
            return 201, storage.create_project(data)
        if len(parts) == 3 and parts[:2] == ["api", "projects"]:
            project_id = parts[2]
            if method == "GET":
                project = storage.get_project(project_id)
                return (200, project) if project else (404, {"error": "Project not found."})
            if method in {"PUT", "PATCH"}:
                data = self.read_json()
                validation_error = validate_project_ai_configuration(data, storage.list_integration_connections())
                if validation_error:
                    return 400, {"error": validation_error}
                project = storage.update_project(project_id, data)
                return (200, project) if project else (404, {"error": "Project not found."})
            if method == "DELETE":
                if not storage.delete_project(project_id):
                    return 404, {"error": "Project not found."}
                return 204, None
        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "translation-rules" and method in {"PUT", "PATCH"}:
            data = self.read_json()
            translation_rules = data.get("translationRules", "")
            if not isinstance(translation_rules, str):
                return 400, {"error": "Translation rules must be text."}
            project = storage.update_project_translation_rules(parts[2], translation_rules)
            return (200, project) if project else (404, {"error": "Project not found."})
        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "translation-glossaries":
            if method == "GET":
                return 200, translation_service.list_project_glossaries(parts[2])
            if method in {"POST", "PUT"}:
                return 200, translation_service.save_project_glossary(parts[2], self.read_json())
        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "translation-glossaries" and parts[4] == "commit" and method == "POST":
            return 200, translation_service.commit_project_glossary_draft(parts[2], self.read_json())
        if len(parts) == 6 and parts[:3] == ["api", "projects", parts[2]] and parts[3] == "chapters" and parts[5] == "analysis" and method == "POST":
            return 200, translation_service.analyze_chapter(parts[2], parts[4], self.read_json())
        if len(parts) == 6 and parts[:2] == ["api", "projects"] and parts[3] == "translation-glossaries" and parts[5] == "current-version" and method == "GET":
            return 200, translation_service.get_project_glossary_current_version(parts[2], parts[4])
        if len(parts) == 7 and parts[:2] == ["api", "projects"] and parts[3] == "translation-glossaries" and parts[5] == "versions" and method == "GET":
            return 200, translation_service.materialize_project_glossary_version(parts[2], parts[4], parts[6])
        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "cover" and method == "DELETE":
            if not storage.clear_project_cover(parts[2]):
                return 404, {"error": "Book document not found."}
            return 204, None
        if len(parts) == 5 and parts[:3] == ["api", "projects", parts[2]] and parts[3] == "book" and parts[4] == "structure":
            structure = storage.get_book_structure(parts[2])
            return (200, structure) if structure else (404, {"error": "Book structure not found."})
        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "brief":
            project_id = parts[2]
            if method == "GET":
                return 200, storage.list_project_brief_entries(project_id)
            if method == "POST":
                return 201, storage.create_project_brief_entry(project_id, self.read_json())
        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "brief":
            entry_id = parts[4]
            if method in {"PUT", "PATCH"}:
                entry = storage.update_project_brief_entry(entry_id, self.read_json())
                return (200, entry) if entry else (404, {"error": "Brief entry not found."})
        if len(parts) == 3 and parts[:2] == ["api", "paragraphs"] and method in {"PUT", "PATCH"}:
            data = self.read_json()
            paragraph = storage.update_paragraph(parts[2], data.get("translationText"), bool(data.get("reviewed", False)))
            return (200, paragraph) if paragraph else (404, {"error": "Paragraph not found."})
        if len(parts) == 4 and parts[:2] == ["api", "paragraphs"] and parts[3] == "translate" and method == "POST":
            return 200, translation_service.translate_paragraph(parts[2], self.read_json())
        if (
            len(parts) == 6
            and parts[0] == "api"
            and parts[1] == "projects"
            and parts[3] == "chapters"
            and parts[5] == "translate"
            and method == "POST"
        ):
            return 200, translation_service.translate_chapter(parts[2], parts[4], self.read_json())
        if len(parts) == 4 and parts[:2] == ["api", "chapters"] and parts[3] == "title" and method in {"PUT", "PATCH"}:
            data = self.read_json()
            chapter = storage.update_chapter_title(parts[2], data.get("translationTitle"), bool(data.get("reviewed", False)))
            return (200, chapter) if chapter else (404, {"error": "Chapter title not found."})
        return 404, {"error": "API route not found."}

    def handle_api_request(self, method):
        path = urlparse(self.path).path
        try:
            status, payload = self.handle_api(method, path)
            self.send_json(status, payload)
        except IntegrationServiceError as error:
            self.send_json(error.http_status, {"error": str(error), "code": error.code})
        except TranslationServiceError as error:
            self.send_json(error.http_status, {"error": str(error), "code": error.code})
        except sqlite3.IntegrityError as error:
            self.send_json(409, {"error": "Entity or relationship already exists or references an unknown entity."})
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
        except Exception:
            self.send_json(500, {"error": "Persistence request failed."})

    def do_POST(self):
        if self.path.startswith("/api/"):
            path = urlparse(self.path).path.split("/")
            if len(path) == 6 and path[1:4] == ["api", "projects", path[3]] and path[4] == "book" and path[5] == "archive":
                try:
                    data = self.read_json()
                    filename, content = storage.create_book_archive(path[3], data.get("translations"))
                    self.send_download(filename, content)
                except ValueError as error:
                    self.send_json(404, {"error": str(error)})
                return
            if len(path) == 5 and path[1] == "api" and path[2] == "projects" and path[4] == "cover":
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if size <= 0:
                        raise ValueError("Файл не було передано.")
                    if size > 10 * 1024 * 1024:
                        raise ValueError("Файл завеликий. Максимальний розмір для обкладинки: 10 МБ.")
                    content_type = self.headers.get("Content-Type", "")
                    if not content_type.startswith("multipart/form-data"):
                        raise ValueError("Очікується завантаження зображення.")
                    _, content = parse_multipart(content_type, self.rfile.read(size))
                    if self._detect_image_type(content) == "application/octet-stream":
                        raise ValueError("Підтримуються зображення JPEG, PNG, GIF або WebP.")
                    if not storage.set_project_cover(path[3], content):
                        raise ValueError("Книга для цього проєкту не знайдена.")
                    self.send_json(200, {"success": True})
                except ValueError as error:
                    self.send_json(400, {"success": False, "error": str(error)})
                return
            self.handle_api_request("POST")
            return
        if self.path != "/upload":
            self.send_json(404, {"success": False, "error": "Запитуваний маршрут не знайдено."})
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0:
                raise ValueError("Файл не було передано.")
            if size > MAX_UPLOAD_SIZE:
                raise ValueError("Файл завеликий. Максимальний розмір: 50 МБ.")
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                raise ValueError("Очікується завантаження файлу.")
            filename, content = parse_multipart(content_type, self.rfile.read(size))
            extension = Path(filename).suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                raise ValueError("⚠️ Ой-ой-ой! Цей файл не підходить для аналізу. Workbench працює з EPUB. Підготуй книгу у форматі EPUB і завантаж її ще раз. DOCX використовується як робочий/фінальний формат, але для аналізу книги потрібен EPUB.")

            data = parse_epub(filename, content)
            project_id = self.headers.get("X-Project-Id")
            if project_id:
                data = storage.save_book_structure(
                    project_id,
                    filename,
                    "application/epub+zip",
                    content,
                    data,
                )
            self.send_json(200, {"success": True, "data": data})
        except ValueError as error:
            self.send_json(400, {"success": False, "error": str(error)})
        except Exception:
            self.send_json(422, {"success": False, "error": "Не вдалося розібрати файл. Перевірте, що він не пошкоджений."})

    def do_GET(self):
        if self.path.startswith("/api/"):
            path = urlparse(self.path).path.split("/")
            if len(path) == 4 and path[1:3] == ["api", "inline-images"]:
                image = storage.get_inline_image(path[3])
                if image is None:
                    self.send_json(404, {"error": "Inline image not found."})
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", image["mimeType"])
                    self.send_header("Content-Length", str(len(image["data"])))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(image["data"])
                return
            # Handle cover image endpoint
            if len(path) == 5 and path[1] == "api" and path[2] == "projects" and path[4] == "cover":
                try:
                    cover = storage.get_project_cover(path[3])
                    if cover is None:
                        self.send_json(404, {"error": "Cover not found."})
                    else:
                        # Detect image format
                        content_type = self._detect_image_type(cover)
                        self.send_response(200)
                        self.send_header("Content-Type", content_type)
                        self.send_header("Content-Length", str(len(cover)))
                        self.send_header("Cache-Control", "public, max-age=86400")
                        self.end_headers()
                        self.wfile.write(cover)
                except Exception:
                    self.send_json(500, {"error": "Failed to retrieve cover."})
                return
            self.handle_api_request("GET")
            return
        super().do_GET()

    def _detect_image_type(self, data):
        """Detect image type from binary data."""
        if len(data) < 4:
            return "application/octet-stream"
        if data[:2] == b'\xff\xd8':
            return "image/jpeg"
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        if data[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        if data[:4] == b'RIFF' and len(data) >= 12 and data[8:12] == b'WEBP':
            return "image/webp"
        return "application/octet-stream"

    def do_PUT(self):
        if self.path.startswith("/api/"):
            self.handle_api_request("PUT")
            return
        self.send_json(405, {"error": "Method not allowed."})

    def do_PATCH(self):
        if self.path.startswith("/api/"):
            self.handle_api_request("PATCH")
            return
        self.send_json(405, {"error": "Method not allowed."})

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self.handle_api_request("DELETE")
            return
        self.send_json(405, {"error": "Method not allowed."})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = ThreadingHTTPServer((HOST, port), WorkbenchHandler)
    print(f"Translation Workbench доступний за адресою http://{HOST}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер зупинено.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
