import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import stale_pages


def commit(sha, subject, parents=1):
    return {"sha": sha * 7, "commit": {"message": subject + "\n\nbody"},
            "parents": [{}] * parents, "html_url": f"https://x/{sha}"}


class StaleChecks(unittest.TestCase):
    def test_parse_watch_defaults_owner(self):
        self.assertEqual(("panxiao81/homelab-infra", "apps/x"), stale_pages.parse_watch("homelab-infra:apps/x/"))
        self.assertEqual(("o/r", "a.md"), stale_pages.parse_watch("o/r:a.md"))

    def test_commits_skip_merges_and_dependency_bumps(self):
        data = [commit("a", "feat: real"), commit("b", "Merge pull request x", 2),
                commit("c", "chore(deps): update y"), commit("d", "fix(deps): pin")]
        with mock.patch.object(stale_pages, "api", return_value=data) as api:
            found = stale_pages.commits_since("o/r", "apps/x", date(2026, 11, 18))
        self.assertEqual([("aaaaaaa", "feat: real", "https://x/a")], found)
        self.assertIn("since=2026-11-18T00%3A00%3A00Z", api.call_args[0][0])
