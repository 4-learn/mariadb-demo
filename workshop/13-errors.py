"""Stdlib-only unit evidence. These mocks do NOT prove MariaDB behavior."""
from contextlib import closing
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import course_db


class ResourceTests(unittest.TestCase):
    def test_success_commits_and_closes_both_cursors(self):
        conn = MagicMock(autocommit=True)
        first, second = MagicMock(), MagicMock()
        conn.cursor.side_effect = [first, second]
        result = course_db.create_product_with_document(conn, "P912", "test", "D001")
        self.assertEqual(result, {"product_id": "P912", "document_id": "D001", "committed": True})
        conn.begin.assert_called_once()
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()
        first.close.assert_called_once()
        second.close.assert_called_once()

    def test_second_failure_rolls_back_and_closes(self):
        conn = MagicMock(autocommit=True)
        first, second = MagicMock(), MagicMock()
        second.execute.side_effect = RuntimeError("simulated FK failure")
        conn.cursor.side_effect = [first, second]
        with self.assertRaises(RuntimeError):
            with closing(conn):
                course_db.create_product_with_document(conn, "P913", "test", "D999")
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()
        first.close.assert_called_once()
        second.close.assert_called_once()
        conn.close.assert_called_once()

    def test_connection_failure_has_no_connection_to_close(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "app.json"
            config.write_text(json.dumps(dict(user="course_app", password="test-only",
                database=course_db.DATABASE, unix_socket="/nonexistent/course.sock")))
            config.chmod(0o600)
            driver = SimpleNamespace(connect=MagicMock(side_effect=RuntimeError("connect failed")))
            with patch.dict("sys.modules", {"mariadb": driver}):
                with self.assertRaisesRegex(RuntimeError, "connect failed"):
                    course_db.connect(config)
            driver.connect.assert_called_once_with(user="course_app", password="test-only",
                database=course_db.DATABASE, unix_socket="/nonexistent/course.sock", autocommit=True)

    def test_cursor_failure_still_closes_connection(self):
        conn = MagicMock()
        conn.cursor.side_effect = RuntimeError("cursor unavailable")
        with self.assertRaises(RuntimeError):
            with closing(conn):
                course_db.get_product(conn, "P001")
        conn.close.assert_called_once()

    def test_quote_is_bound_not_interpolated(self):
        conn = MagicMock()
        conn.cursor.return_value.fetchone.return_value = None
        value = "P001' OR 1=1 -- "
        self.assertIsNone(course_db.get_product(conn, value))
        sql, parameters = conn.cursor.return_value.execute.call_args.args
        self.assertNotIn(value, sql)
        self.assertEqual(parameters, (value,))


if __name__ == "__main__":
    unittest.main()
