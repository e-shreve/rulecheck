"""
    File Manager Module

    Contains the FileManager class which handles iteration over files to be checked.
"""

import glob
from pathlib import Path
import sys

from rulecheck.file import File
from rulecheck.ignore import IgnoreFile
from rulecheck.rule_manager import RuleManager
from rulecheck.srcml import Srcml
from rulecheck.logger import Logger
from rulecheck.rule import LogType
from rulecheck.rule import LogFilePosition
from rulecheck.verbose import Verbose

class FileManager:
    """Processes globs to select files to pass to a RuleManager."""

    def __init__(self, rules:RuleManager, srcml:Srcml, logger:Logger):
        self._rules = rules
        self._srcml = srcml
        self._logger = logger
        self._current_file = None
        self._file_count = 0
        self._ignore_file_out = None

    def set_ignore_file_out(self, ignore_file_out:IgnoreFile):
        """Sets the ignore file being output. If it exists, the flush() method will be called on it
           after each file is processed."""

        self._ignore_file_out = ignore_file_out

    def process_files(self, globs:[str]):
        """Handles iteration over globs and passes individual file paths to process_file() for
           processing."""

        if (not globs is None) and len(globs) > 0:
            # Handle STDIN input
            if len(globs) == 1 and globs[0] == "-":
                for file_path in sys.stdin:
                    self.process_file(file_path.rstrip())
            # Otherwise, handle glob input
            else:
                for glob_str in globs:
                    for file_path in glob.iglob(glob_str, recursive=True):
                        self.process_file(file_path)

    def process_file(self, file_path:str):
        """Obtains srcml of file located at file_path and runs configured rules it."""

        self._current_file = None

        if Path(file_path).is_dir():
            return

        try:
            file_stream = open(file_path, 'r', newline='')
            try:
                Verbose.print("Opened file for checking: " + file_path)
                self._current_file = File(file_path,
                                          file_stream.readlines(),
                                          self._srcml.get_srcml(file_path))
                self._file_count += 1
                self._rules.run_rules_on_file(self._current_file)
            finally:
                file_stream.close()
                if self._ignore_file_out:
                    self._ignore_file_out.flush()
        except (IOError, OSError) as exc:
            self.log_file_exception("Could not open file! See stderr.", exc, file_path)


    def get_file_count(self) -> int:
        """Returns the total number files processed."""
        return self._file_count

    def log_file_exception(self, msg:str, exc:Exception, file_name:str):
        """ Wrapper used to log issues when working with a file.
        """

        self._logger.log_violation(LogType.ERROR, LogFilePosition(-1,-1), msg, False, file_name,
                             "rulecheck", [])
        print(exc, file=sys.stderr)
