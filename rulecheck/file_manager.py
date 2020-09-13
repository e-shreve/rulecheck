import glob
from pathlib import Path
import sys

from rulecheck.file import File
from rulecheck.rule_manager import RuleManager
from rulecheck.srcml import Srcml
from rulecheck.logger import Logger
from rulecheck.rule import LogType
from rulecheck.rule import LogFilePosition

#pylint: disable=missing-function-docstring
#pylint: disable=too-many-arguments
#pylint: disable=too-many-instance-attributes

class FileManager:
    def __init__(self, rules:RuleManager, srcml:Srcml, logger:Logger, verbose:bool):
        self._rules = rules
        self._srcml = srcml
        self._logger = logger
        self._current_file = None
        self._file_count = 0
        self.verbose = verbose

    def print_verbose(self, message:str):
        if self.verbose:
            print(message)

    def process_files(self, globs:[str]):

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
        self._current_file = None

        if Path(file_path).is_dir():
            return

        try:
            file_stream = open(file_path, 'r', newline='')
            try:
                self.print_verbose("Opened file for checking: " + file_path)
                self._current_file = File(file_path,
                                          file_stream.readlines(),
                                          self._srcml.get_srcml(file_path))
                self._file_count += 1
                self._rules.run_rules_on_file(self._current_file)
            finally:
                file_stream.close()
        except (IOError, OSError) as exc:
            self.log_file_exception("Could not open file! See stderr.", exc, file_path)


    def get_file_count(self) -> int:
        return self._file_count

    def log_file_exception(self, msg:str, exc:Exception, file_name:str):
        """ Wrapper used to log issues when working with a file.
        """

        self._logger.log_violation(LogType.ERROR, LogFilePosition(-1,-1), msg, False, file_name,
                             "rulecheck", [])
        print(exc, file=sys.stderr)
