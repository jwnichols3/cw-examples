import unittest
from unittest.mock import patch
import importlib
import logging
import common.logging_utilities


class TestLoggingUtilities(unittest.TestCase):
    def setUp(self):
        # Reload logging and logging_utilities modules to reset logging configuration
        importlib.reload(logging)
        importlib.reload(common.logging_utilities)

    @patch("os.getenv", return_value="DEBUG")
    def test_setup_logging_with_debug_level(self, mock_getenv):
        logger = common.logging_utilities.setup_logging()
        self.assertEqual(logger.level, logging.DEBUG)

    @patch("os.getenv", return_value="INFO")
    def test_setup_logging_with_info_level(self, mock_getenv):
        logger = common.logging_utilities.setup_logging()
        self.assertEqual(logger.level, logging.INFO)


if __name__ == "__main__":
    unittest.main()
