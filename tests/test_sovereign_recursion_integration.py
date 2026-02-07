import json
import tempfile
import unittest
from pathlib import Path

from sovereign_recursion.ledger import UniversalLedger


class TestSovereignRecursionLedger(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp.name) / "ledger.jsonl"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_append_and_verify(self) -> None:
        ledger = UniversalLedger(self.ledger_path)
        h1 = ledger.append("test", "check", {"status": "STABLE", "n": 1})
        h2 = ledger.append("test", "check", {"status": "DEGRADED", "n": 2})
        self.assertTrue(isinstance(h1, str) and len(h1) == 64)
        self.assertTrue(isinstance(h2, str) and len(h2) == 64)

        report = ledger.verify()
        self.assertTrue(report.get("ok"), msg=json.dumps(report, indent=2))
        self.assertEqual(report.get("total_entries"), 2)

    def test_tamper_detection(self) -> None:
        ledger = UniversalLedger(self.ledger_path)
        ledger.append("test", "check", {"status": "STABLE"})

        # Tamper by appending a malformed line
        self.ledger_path.write_text(self.ledger_path.read_text(encoding="utf-8") + "{not-json\n", encoding="utf-8")

        report = ledger.verify()
        self.assertFalse(report.get("ok"))


if __name__ == "__main__":
    unittest.main()
