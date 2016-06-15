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

    def tearDown(self):
        sys.exit = _ORIGINAL_SYS_EXIT
        for temp_file in self.temp_files:
            os.remove(temp_file)

    def get_temp_file(self, temp_directory, lines):
        file_content = "".join(lines)
        print(file_content)
        temp_file = tempfile.NamedTemporaryFile(dir=temp_directory)
        temp_file.write(file_content)
        temp_file.flush()

        return temp_file

    def get_archive_file(self, lines):
        return self.get_multi_file_archive([lines])

    def get_multi_file_archive(self, files_lines):
        temp_directory = tempfile.mkdtemp()

        test_archive_files = []
        for file_lines in files_lines:
            test_archive_files.append(self.get_temp_file(temp_directory, file_lines))

        temp_tar_file = tempfile.mkstemp()
        temp_tar_file_name = temp_tar_file[1]

        self.temp_files.append(temp_tar_file_name)

        with tarfile.open(temp_tar_file_name, "w") as archive_file:
            for temp_file in test_archive_files:
                archive_file.add(temp_file.name)
            archive_file.close()

        return archive_file

    # def get_nested_multi_file_archive(self, files_lines):

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

    def test_parsing_subject_returns_correct_data(self):
        test_archive_file = self.get_archive_file(
            ["Subject: PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5\n"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([
            {"subject": "PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5"}], result)

    def test_parsing_subject_ignores_case(self):
        test_archive_file = self.get_archive_file(
            ["SuBjeCT: PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5"])

        result = parse_archive(test_archive_file.name)
        self.assertEqual([
            {"subject": "PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5"}], result)

    def test_parsing_subject_accepts_no_space_delimeter(self):
        test_archive_file = self.get_archive_file(
            ["Subject:PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([
            {"subject": "PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5"}], result)

    def test_parsing_subject_accepts_extra_space(self):
        test_archive_file = self.get_archive_file(
            ["Subject:      PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5"])

        result = parse_archive(test_archive_file.name)

        self.assertEqual([
            {"subject": "PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5"}], result)

    def test_parsing_subject_accepts_multiple_lines(self):
        test_archive_file = self.get_archive_file(
            ["Subject:PREVIEW:   Save $170 and get \n\t\tspecial gift with \n\t\tCorelDraw Premium"
                "Suite X5"])
        result = parse_archive(test_archive_file.name)

        self.assertEqual([
            {"subject": "PREVIEW:   Save $170 and get special gift with CorelDraw Premium"
                "Suite X5"}], result)

    def test_parsing_returns_correct_data_from_multi_file_archive(self):
        files_contents = [
            ["Date: date1\n", "Subject: subject1\n", "From: from1\n"],
            ["Date: date2\n", "Subject: subject2\n", "From: from2\n"],
            ["Date: date3\n", "Subject: subject3\n", "From: from3\n"],
        ]
        test_archive_file = self.get_multi_file_archive(files_contents)

        result = parse_archive(test_archive_file.name)

        self.assertEqual([
            {"date": "date1", "from": "from1", "subject": "subject1"},
            {"date": "date2", "from": "from2", "subject": "subject2"},
            {"date": "date3", "from": "from3", "subject": "subject3"}], result)
