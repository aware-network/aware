"""a6 documentation observed through actual installed setup and owner results."""
import json
import os
from pathlib import Path
import tempfile
import unittest

import test_installed_workflow as flow

BINDING = json.loads(Path(os.environ["AWARE_REPAIR_BINDING"]).read_bytes())


class InstalledFeedback(unittest.TestCase):
    def test_advertised_labels_and_clarifications_in_actual_scaffold(self):
        with tempfile.TemporaryDirectory(prefix="aware-feedback-scaffold-") as temporary:
            parent = Path(temporary)
            root = parent / "customer"
            flow.invoke(parent, "init", "--repository-root", str(root), "--create-repository")
            observed = flow.invoke(root, "contract")
            version = BINDING["consumer_contract"]["version"]
            self.assertEqual(observed["version"], version)
            self.assertIn("**" + version + "**", (root / "AGENTS.md").read_text())
            self.assertIn("`aware.agent.fs.v1` / " + version + ".", (root / "docs/agents/README.md").read_text())
            issue = (root / "docs/issues/PROTOCOL.md").read_text()
            for term in ["issue_day_index:pending", "feed:unavailable", "shared_index_projection", "no operation that evaluates or checks"]:
                self.assertIn(term, issue)

    def test_actual_projection_statuses_and_closed_criteria_remain_distinct(self):
        # Reuse fixture setup/helpers, not the owner's decision logic or tests.
        fixture = flow.InstalledWorkflow()
        fixture.setUp()
        try:
            opened = fixture.open()
            for receipt in opened["receipts"]:
                self.assertIn("projection_effect:issue_day_index:pending", receipt["evidence"])
                self.assertIn("projection_effect:feed:unavailable", receipt["evidence"])
            (fixture.root / "src/result.py").write_text("value = 2\n")
            self.assertEqual(fixture.commit("src/result.py", flow.ISSUE, dry=True)["outcome"], "planned")
            published = fixture.commit("src/result.py", flow.ISSUE)
            self.assertEqual(published["shared_index_projection"], "applied")
            self.assertFalse(published["index_reconciliation_pending"])
            self.assertEqual(flow.git(fixture.root, "status", "--porcelain", "--", "src/result.py", flow.ISSUE), "")
            closed = flow.mutation(fixture.root, "close", "--resolution", "Fixture value=2 delivered",
                                   "--verified-by", "Actual installed fixture asserts value=2",
                                   "--publication-receipt-ref", published["publication_receipt_ref"])
            self.assertEqual(closed["outcome"], "applied")
            observed = fixture.observe()["projection"]
            self.assertEqual(observed["identity"]["status"], "closed")
            self.assertEqual(observed["content"]["acceptance_items"][0]["checked"], False)
            self.assertIn("projection_effect:issue_day_index:pending", closed["evidence"])
            self.assertEqual(flow.git(fixture.root, "status", "--porcelain", "--", "src/result.py", flow.ISSUE), "")
        finally:
            fixture.tearDown()


if __name__ == "__main__":
    unittest.main()
