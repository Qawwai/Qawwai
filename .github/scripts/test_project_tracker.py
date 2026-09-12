import unittest
from unittest.mock import Mock

from project_tracker import START, END, refresh


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.line = '- **[PCA](https://github.com/Qawwai/pca-image-compression)** — My wording.'
        self.content = 'Personal intro\n' + START + '\n' + self.line + '\n' + END + '\nMy footer\n'
        self.fetch = Mock(return_value='2026-09-12')

    def test_only_updates_project_line(self):
        self.assertEqual(refresh(self.content, self.fetch), self.content.replace(self.line, self.line + ' · Updated 2026-09-12.'))

    def test_idempotent(self):
        once = refresh(self.content, self.fetch)
        self.assertEqual(refresh(once, self.fetch), once)

    def test_deleted_section_stays_deleted(self):
        self.assertEqual(refresh('My edited profile\n', self.fetch), 'My edited profile\n')
        self.fetch.assert_not_called()

    def test_deleted_project_stays_deleted(self):
        content = self.content.replace(self.line, '')
        self.assertEqual(refresh(content, self.fetch), content)
        self.fetch.assert_not_called()

    def test_unlisted_project_untouched(self):
        content = self.content.replace('pca-image-compression', 'other-repository')
        self.assertEqual(refresh(content, self.fetch), content)
        self.fetch.assert_not_called()

    def test_api_failure_aborts(self):
        with self.assertRaises(OSError):
            refresh(self.content, Mock(side_effect=OSError('Unavailable')))

    def test_malformed_markers_fail(self):
        for content in (START, END, END + START, START + START + END):
            with self.assertRaises(ValueError):
                refresh(content, self.fetch)

    def test_crlf_preserved(self):
        content = self.content.replace('\n', '\r\n')
        self.assertEqual(refresh(content, self.fetch).count('\r\n'), content.count('\r\n'))

    def test_no_push_preserves_line(self):
        self.assertEqual(refresh(self.content, Mock(return_value=None)), self.content)


if __name__ == '__main__':
    unittest.main()
