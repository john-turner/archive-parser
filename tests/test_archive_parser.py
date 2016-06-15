import unittest
import sys
import mock
import tempfile
import tarfile
import os

from archive_parser import main, InvalidArchiveFile, parse_archive

_ORIGINAL_SYS_EXIT = sys.exit


class SysExitCalled(Exception):
    pass


class TestArchiveParser(unittest.TestCase):
    def setUp(self):
        sys.exit = self._check_sys_exit
        self.temp_files = []
        self.default_entries = {
            "date": "Date: Fri, 01 Apr 2011 05:52:55 PDT\n",
            "from": "From: Corel <news@email1-corel.com>\n",
            "subject": "Subject: PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
            "Suite X5\n"
        }

    def tearDown(self):
        sys.exit = _ORIGINAL_SYS_EXIT
        for temp_file in self.temp_files:
            os.remove(temp_file)

    def get_archive_file(self, lines):
        temp_directory = tempfile.mkdtemp()

        file_content = "".join(lines)

        temp_file_one = tempfile.NamedTemporaryFile(dir=temp_directory)
        temp_file_one.write(file_content)
        temp_file_one.flush()

        temp_tar_file = tempfile.mkstemp()
        temp_tar_file_name = temp_tar_file[1]

        self.temp_files.append(temp_tar_file_name)

        with tarfile.open(temp_tar_file_name, "w") as archive_file:
            archive_file.add(temp_file_one.name)
            archive_file.close()

        return archive_file

    def _check_sys_exit(self, exit_code):
        self._exit_code = exit_code
        raise SysExitCalled(exit_code)

    def test_archive_parser_requires_archive_argument(self):
        sys.argv = ["archive_parser.py"]
        with self.assertRaises(SysExitCalled):
            main()

    @mock.patch("os.path.isfile")
    def test_archive_parser_requires_valid_file_path(self, mock_isfile):
        sys.argv = ["archive_parser.py", "archives/test.msg"]
        mock_isfile.return_value = False

        with self.assertRaises(InvalidArchiveFile):
            main()

    @mock.patch("archive_parser.parse_archive")
    def test_archive_parser_passes_correct_file_path_to_extractor(self, mock_extractor):
        temp_file = tempfile.NamedTemporaryFile()
        sys.argv = ["archive_parser.py", temp_file.name]
        main()
        mock_extractor.assert_called_with(temp_file.name)

    def test_parse_archive_raises_on_non_tar_file(self):
        temp_file = tempfile.NamedTemporaryFile()

        with self.assertRaises(InvalidArchiveFile):
            parse_archive(temp_file.name)

    def test_parsing_returns_correct_date(self):
        test_archive_file = self.get_archive_file(
            ["Date: Fri, 01 Apr 2011 05:52:55 PDT\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"date": "Fri, 01 Apr 2011 05:52:55 PDT"}], result)

    def test_parsing_date_ignores_case(self):
        test_archive_file = self.get_archive_file(
            ["date: Fri, 01 Apr 2011 05:52:55 PDT\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"date": "Fri, 01 Apr 2011 05:52:55 PDT"}], result)

    def test_parsing_date_accepts_no_space_delimeter(self):
        test_archive_file = self.get_archive_file(
            ["date:Fri, 01 Apr 2011 05:52:55 PDT\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"date": "Fri, 01 Apr 2011 05:52:55 PDT"}], result)

    def test_parsing_date_accepts_extra_space(self):
        test_archive_file = self.get_archive_file(
            ["date:      Fri, 01 Apr 2011 05:52:55 PDT\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"date": "Fri, 01 Apr 2011 05:52:55 PDT"}], result)

    def test_parsing_date_accepts_multiple_lines(self):
        test_archive_file = self.get_archive_file(
            ["date: Fri, 01 Apr 2011 \n\t\t05:52:55 PDT\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"date": "Fri, 01 Apr 2011 05:52:55 PDT"}], result)

    def test_parsing_ignores_body(self):
        test_archive_file = self.get_archive_file(
            ["\n", "date: Fri, 02 Apr 2011 \n\t\t05:52:55 PDT\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{}], result)

    def test_parsing_ignores_non_parsed_header_continuation(self):
        test_archive_file = self.get_archive_file([
            "test: test \n\t\t test\n",
            "date: Fri, 02 Apr 2011 \n\t\t05:52:55 PDT\n",
            "test1: test1 \n\t\t test1\n"
        ])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"date": "Fri, 02 Apr 2011 05:52:55 PDT"}], result)

    def test_parsing_from_returns_correct_data(self):
        test_archive_file = self.get_archive_file(
            ["From: Corel <news@email1-corel.com>\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"from": "Corel <news@email1-corel.com>"}], result)

    def test_parsing_from_ignores_case(self):
        test_archive_file = self.get_archive_file(
            ["from: Corel <news@email1-corel.com>\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"from": "Corel <news@email1-corel.com>"}], result)

    def test_parsing_from_accepts_no_space_delimeter(self):
        test_archive_file = self.get_archive_file(
            ["from:Corel <news@email1-corel.com>\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"from": "Corel <news@email1-corel.com>"}], result)

    def test_parsing_from_accepts_extra_space(self):
        test_archive_file = self.get_archive_file(
            ["from:           Corel <news@email1-corel.com>\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"from": "Corel <news@email1-corel.com>"}], result)

    def test_parsing_from_accepts_multiple_lines(self):
        test_archive_file = self.get_archive_file(
            ["from:           Corel \n\t\t<news@email1-corel.com>\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"from": "Corel <news@email1-corel.com>"}], result)

    def test_parses_subject_correctly(self):
        test_archive_file = self.get_archive_file(
            ["From: Corel <news@email1-corel.com>\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([{"from": "Corel <news@email1-corel.com>"}], result)
