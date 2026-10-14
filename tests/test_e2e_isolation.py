"""The e2e server must never touch the application's own database or logs, and must only delete what it made."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from backend import logging_utils, storage
from e2e import e2e_db


class DatabasePathTests(unittest.TestCase):
    def test_default_path_is_the_applications_database_when_nothing_is_set(self):
        self.assertEqual(storage.database_path_from_environment({}), storage.DEFAULT_DATABASE_PATH)
        self.assertEqual(storage.database_path_from_environment({"WORKBENCH_DATABASE_PATH": "  "}), storage.DEFAULT_DATABASE_PATH)
        self.assertEqual(storage.DEFAULT_DATABASE_PATH.name, "workbench.sqlite3")
        self.assertEqual(storage.DEFAULT_DATABASE_PATH.parent.name, "database")

    def test_the_variable_overrides_the_path(self):
        self.assertEqual(storage.database_path_from_environment({"WORKBENCH_DATABASE_PATH": "/tmp/x/e2e.sqlite3"}), Path("/tmp/x/e2e.sqlite3"))

    def test_the_server_module_picks_the_variable_up_at_import(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "isolated.sqlite3"
            logs = Path(directory) / "logs"
            code = "from backend import storage, logging_utils; print(storage.DATABASE_PATH); print(logging_utils.LOG_DIR)"
            result = subprocess.run(
                [sys.executable, "-c", code], capture_output=True, text=True, check=True,
                env={**os.environ, "WORKBENCH_DATABASE_PATH": str(database), "WORKBENCH_LOG_DIR": str(logs)},
            )
            self.assertEqual(result.stdout.split(), [str(database), str(logs)])
            self.assertFalse(database.exists())  # importing does not create the file by itself

    def test_log_directory_default_and_override(self):
        self.assertEqual(logging_utils.DEFAULT_LOG_DIR.name, "logs")
        self.assertEqual(logging_utils.DEFAULT_LOG_DIR.parent, storage.DEFAULT_DATABASE_PATH.parent.parent)


class GuardTests(unittest.TestCase):
    def test_guard_knows_the_same_database_as_the_application(self):
        self.assertEqual(e2e_db.PROTECTED_DATABASE, storage.DEFAULT_DATABASE_PATH.resolve())

    def test_refuses_the_applications_database_and_everything_in_database_and_logs(self):
        database_dir = storage.DEFAULT_DATABASE_PATH.parent
        for unsafe in (
            storage.DEFAULT_DATABASE_PATH,
            database_dir / "other.sqlite3",
            database_dir / "sub" / "x.sqlite3",
            database_dir.parent / "logs" / "x.sqlite3",
            database_dir / ".." / "database" / "workbench.sqlite3",
        ):
            with self.assertRaises(e2e_db.UnsafeE2ePath, msg=str(unsafe)):
                e2e_db.check_database_path(unsafe)

    def test_refuses_a_symlink_that_points_at_the_applications_database(self):
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / "innocent.sqlite3"
            link.symlink_to(storage.DEFAULT_DATABASE_PATH)
            with self.assertRaises(e2e_db.UnsafeE2ePath):
                e2e_db.check_database_path(link)
            linked_directory = Path(directory) / "linked"
            linked_directory.symlink_to(storage.DEFAULT_DATABASE_PATH.parent, target_is_directory=True)
            with self.assertRaises(e2e_db.UnsafeE2ePath):
                e2e_db.check_database_path(linked_directory / "e2e.sqlite3")

    def test_refuses_a_file_that_is_not_a_sqlite3_file(self):
        with self.assertRaises(e2e_db.UnsafeE2ePath):
            e2e_db.check_database_path(Path(tempfile.gettempdir()) / "e2e.db")

    def test_accepts_a_database_outside_the_application_data(self):
        path = Path(tempfile.gettempdir()) / "somewhere" / "e2e.sqlite3"
        self.assertEqual(e2e_db.check_database_path(path), path.resolve())

    def test_refuses_log_directories_of_the_application_and_its_parents(self):
        for unsafe in (storage.DEFAULT_DATABASE_PATH.parent.parent / "logs", storage.DEFAULT_DATABASE_PATH.parent.parent / "logs" / "x",
                       storage.DEFAULT_DATABASE_PATH.parent, e2e_db.REPO_ROOT, Path("/")):
            with self.assertRaises(e2e_db.UnsafeE2ePath, msg=str(unsafe)):
                e2e_db.check_log_directory(unsafe)

    def test_prepare_makes_a_temporary_directory_and_sets_the_variables(self):
        environ: dict[str, str] = {}
        result = e2e_db.prepare(environ)
        try:
            created = Path(result["created"])
            self.assertTrue(created.name.startswith(e2e_db.TEMPORARY_PREFIX))
            self.assertEqual(Path(environ["WORKBENCH_DATABASE_PATH"]), created.resolve() / "workbench.sqlite3")
            self.assertEqual(Path(environ["WORKBENCH_LOG_DIR"]), created.resolve() / "logs")
            self.assertNotEqual(Path(environ["WORKBENCH_DATABASE_PATH"]), storage.DEFAULT_DATABASE_PATH.resolve())
        finally:
            self.assertTrue(e2e_db.remove_created_directory(Path(result["created"])))
        self.assertFalse(Path(result["created"]).exists())

    def test_prepare_refuses_the_applications_database_even_when_it_is_set_explicitly(self):
        with self.assertRaises(e2e_db.UnsafeE2ePath):
            e2e_db.prepare({"WORKBENCH_DATABASE_PATH": str(storage.DEFAULT_DATABASE_PATH), "WORKBENCH_LOG_DIR": "/tmp/x-logs"})

    def test_prepare_keeps_explicit_paths_and_creates_nothing_to_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            environ = {"WORKBENCH_DATABASE_PATH": str(Path(directory) / "mine.sqlite3"), "WORKBENCH_LOG_DIR": str(Path(directory) / "logs")}
            result = e2e_db.prepare(environ)
            self.assertEqual(result["created"], "")


class DeletionTests(unittest.TestCase):
    def test_deletes_only_a_temporary_directory_it_made(self):
        made = Path(tempfile.mkdtemp(prefix=e2e_db.TEMPORARY_PREFIX))
        (made / "workbench.sqlite3").write_text("x")
        self.assertTrue(e2e_db.remove_created_directory(made))
        self.assertFalse(made.exists())

    def test_never_deletes_the_applications_data_or_other_directories(self):
        with tempfile.TemporaryDirectory() as other:  # a temp directory without the prefix
            (Path(other) / "keep.txt").write_text("x")
            self.assertFalse(e2e_db.remove_created_directory(Path(other)))
            self.assertTrue((Path(other) / "keep.txt").exists())
        for protected in (storage.DEFAULT_DATABASE_PATH.parent, storage.DEFAULT_DATABASE_PATH.parent.parent / "logs", e2e_db.REPO_ROOT, Path(tempfile.gettempdir())):
            before = protected.exists()
            self.assertFalse(e2e_db.remove_created_directory(protected))
            self.assertEqual(protected.exists(), before)

    def test_does_not_follow_a_symlink_with_the_right_name(self):
        with tempfile.TemporaryDirectory() as target:
            (Path(target) / "keep.txt").write_text("x")
            link = Path(tempfile.gettempdir()) / f"{e2e_db.TEMPORARY_PREFIX}link-{os.getpid()}"
            link.symlink_to(target, target_is_directory=True)
            try:
                self.assertFalse(e2e_db.remove_created_directory(link))
                self.assertTrue((Path(target) / "keep.txt").exists())
            finally:
                link.unlink()

    def test_refuses_a_prefixed_directory_outside_the_temp_root(self):
        with tempfile.TemporaryDirectory() as directory:
            nested = Path(directory) / f"{e2e_db.TEMPORARY_PREFIX}nested"
            nested.mkdir()
            # (temp root is the parent of `directory`, not of `nested`)
            self.assertFalse(e2e_db.remove_created_directory(nested))
            self.assertTrue(nested.exists())


if __name__ == "__main__":
    unittest.main()
