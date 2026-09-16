import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_docs import check, metadata_errors, split_frontmatter


class DocumentChecks(unittest.TestCase):
    def run_check(self, documents):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, text in documents.items():
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(text)
            return check(root, list(documents))

    def test_commonmark_links_and_code_examples(self):
        errors = self.run_check({
            "README.md": "[引用][page]\n\n[page]: guide.md#中文-标题\n\n"
                         "![附件](asset.svg)\n\n`[假链接](missing.md)`\n\n"
                         "```md\n[示例](missing.md)\n```\n",
            "guide.md": "# 中文 标题\n",
            "asset.svg": "<svg/>",
        })
        self.assertEqual([], errors)

    def test_broken_reference_and_heading(self):
        errors = self.run_check({"README.md": "[x][r]\n\n[r]: missing.md\n\n[x](#absent)\n"})
        self.assertTrue(any("目标不存在" in e for e in errors))
        self.assertTrue(any("标题锚点不存在" in e for e in errors))

    def test_duplicate_headings_and_html_anchor(self):
        self.assertEqual([], self.run_check({"README.md":
            '# Same\n# Same\n<a id="custom"></a>\n[x](#same-1) [y](#custom)\n'}))

    def test_escaped_paths_tables_and_external_links(self):
        self.assertEqual([], self.run_check({
            "README.md": '| a | b |\n|---|---|\n| [x](a%20b.md) | [web](https://example.invalid) |\n',
            "a b.md": '# Target\n',
        }))

    def test_outside_repository_rejected(self):
        errors = self.run_check({"README.md": "[x](../outside.md)\n"})
        self.assertTrue(any("越出仓库" in e for e in errors))

    def test_frontmatter_dates_and_evidence(self):
        meta, _ = split_frontmatter('---\ntitle: Example\nlifecycle: active\nevidence: live-verified\n'
                                   'last_reviewed: 2026-09-16\nlast_verified: null\n---\n# Title\n')
        self.assertTrue(any("live-verified" in e for e in metadata_errors(meta, required=True)))
        meta['last_verified'] = '2026-09-17'
        self.assertTrue(any("不能晚于" in e for e in metadata_errors(meta, required=True)))
        meta['last_verified'] = '2026-02-30'
        self.assertTrue(any("YYYY-MM-DD" in e for e in metadata_errors(meta, required=True)))

    def test_duplicate_yaml_keys_rejected(self):
        errors = self.run_check({"README.md": '---\ntitle: A\ntitle: B\n---\n'})
        self.assertTrue(errors)

    def test_new_service_requires_metadata_and_index(self):
        errors = self.run_check({"services/new.md": "# New\n", "services/index.md": "# Services\n"})
        self.assertTrue(any("缺少 frontmatter" in e for e in errors))
        self.assertTrue(any("未被 services/index.md" in e for e in errors))


if __name__ == '__main__':
    unittest.main()
