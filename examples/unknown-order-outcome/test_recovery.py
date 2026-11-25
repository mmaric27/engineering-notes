import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


CALLER = Path(__file__).with_name("caller.py").resolve()


def invoke(directory, *args):
    return subprocess.run(
        [sys.executable, str(CALLER), str(directory), *args],
        capture_output=True, text=True, timeout=15,
    )


def rows(path, query):
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        return db.execute(query).fetchall()


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name).resolve()
        self.caller = self.directory / "caller.sqlite"
        self.receiver = self.directory / "receiver.sqlite"

    def first_process_loses_response(self, contract):
        first = invoke(self.directory, contract)
        self.assertEqual(first.returncode, 75, first.stderr)
        [(reference, key, status)] = rows(self.caller, "SELECT * FROM intent")
        self.assertEqual(status, "unknown")
        self.assertEqual(rows(self.receiver, "SELECT * FROM attempts"), [(reference, key)])
        self.assertEqual(rows(self.receiver, "SELECT * FROM orders"), [(reference, key)])
        return reference, key

    def test_keyed_restart_makes_two_submissions_but_one_order(self):
        reference, key = self.first_process_loses_response("keyed")
        self.assertTrue(key)
        second = invoke(self.directory)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(rows(self.receiver, "SELECT * FROM attempts"), [(reference, key)] * 2)
        self.assertEqual(rows(self.receiver, "SELECT * FROM orders"), [(reference, key)])
        self.assertEqual(rows(self.caller, "SELECT * FROM intent"), [(reference, key, "confirmed")])

    def test_unkeyed_restart_reconciles_and_keeps_unknown_without_resubmitting(self):
        reference, key = self.first_process_loses_response("unkeyed")
        self.assertIsNone(key)
        second = invoke(self.directory)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second.stdout.strip(), "not_found_in_read_view")
        self.assertEqual(rows(self.receiver, "SELECT * FROM lookups"), [(reference,)])
        self.assertEqual(rows(self.receiver, "SELECT * FROM attempts"), [(reference, None)])
        self.assertEqual(rows(self.receiver, "SELECT * FROM orders"), [(reference, None)])
        self.assertEqual(rows(self.caller, "SELECT * FROM intent"), [(reference, None, "unknown")])
