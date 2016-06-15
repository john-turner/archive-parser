import unittest
import sys
import mock

from archive_parser import main, InvalidArchiveFile

_ORIGINAL_SYS_EXIT = sys.exit


class SysExitCalled(Exception):
    pass


class TestArchiveParser(unittest.TestCase):
    def setUp(self):
        sys.exit = self._check_sys_exit

    def tearDown(self):
        sys.exit = _ORIGINAL_SYS_EXIT

    def _check_sys_exit(self, exit_code):
        self._exit_code = exit_code
        raise SysExitCalled(exit_code)

    def test_archive_parser_requires_archive_argument(self):
        sys.argv = ["archive_parser.py"]
        with self.assertRaises(SysExitCalled):
            main()

    @mock.patch("os.path.isfile")
    def test_archive_parser_requires_valid_file_path(self, mock_isfile):
        sys.argv = ["archive_parser.py", "/archives/test.msg"]
        mock_isfile.return_value = False

        with self.assertRaises(InvalidArchiveFile):
            main()
