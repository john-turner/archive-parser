import unittest
import sys
import mock
import tempfile
import tarfile
import os

from archive_parser import main, InvalidArchiveFile, archive_extractor

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

    def get_test_archive_file(self):
        temp_directory = tempfile.mkdtemp()

        temp_file_one = tempfile.NamedTemporaryFile(dir=temp_directory)
        temp_file_one.write(
            "Date: Fri, 01 Apr 2011 05:52:55 PDT\n"
            "From: Corel <news@email1-corel.com>\n"
            "Subject: PREVIEW:   Save $170 and get special gift with CorelDraw Premium Suite X5\n"
        )
        temp_file_one.flush()

        temp_file_two = tempfile.NamedTemporaryFile(dir=temp_directory)
        temp_file_two.write(
            "Date: Fri, 01 Apr 2011 05:52:55 PDT\n"
            "From: Corel <news@email1-corel.com>\n"
            "Subject: PREVIEW:   Save $170 and get special gift with CorelDraw Premium Suite X5\n"
        )
        temp_file_two.flush()

        temp_tar_file = tempfile.mkstemp()
        temp_tar_file_name = temp_tar_file[1]

        self.temp_files.append(temp_tar_file_name)

        archive_file = tarfile.open(temp_tar_file_name, "w")
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

    @mock.patch("archive_parser.archive_extractor")
    def test_archive_parser_passes_correct_file_path_to_extractor(self, mock_extractor):
        temp_file = tempfile.NamedTemporaryFile()
        sys.argv = ["archive_parser.py", temp_file.name]
        main()
        mock_extractor.assert_called_with(temp_file.name)

    def test_archive_extractor_raises_on_non_tar_file(self):
        temp_file = tempfile.NamedTemporaryFile()
        with self.assertRaises(InvalidArchiveFile):
            archive_extractor(temp_file.name)

    def test_archive_extractor_returns_correct_date(self):
        test_archive_file = self.get_test_archive_file()
        result = archive_extractor(test_archive_file.name)

        self.assertEqual([{"date": "Fri, 01 Apr 2011 05:52:55 PDT"}], result)
