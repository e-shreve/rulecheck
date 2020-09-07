from decimal import Decimal
import hashlib
import pathlib
import string
import traceback
import typing

# Local imports
from rulecheck.rule import LogType

#pylint: disable=missing-function-docstring
#pylint: disable=too-many-arguments
#pylint: disable=too-many-instance-attributes

def get_ignore_hash(file_name:str,
                    source_line:str, use_leading_whitespace:bool,
                    log_type_name:str,
                    rule_name:str):

    file_name_posix = str(pathlib.Path(file_name).as_posix())

    if source_line:
        if not use_leading_whitespace:
            source_line = source_line.lstrip()
        hash_input = file_name_posix + rule_name + log_type_name + source_line
        ignore_hash = hashlib.md5((hash_input).encode('utf-8')).hexdigest()
    else:
        hash_input = file_name_posix + rule_name + log_type_name
        ignore_hash = hashlib.md5((hash_input).encode('utf-8')).hexdigest()

    return ignore_hash

class IgnoreFilter:
    """ Used to filter log messages. """
    def __init__(self, ignore_list_file_handle:typing.TextIO, verbose:bool):
        self._ignore_list_file_handle = ignore_list_file_handle
        self._rule_ignores = {}
        self._verbose = verbose

    def print_verbose(self, message:str):
        if self._verbose:
            print(message)


    def init_filter(self, file_name:str):
        self._rule_ignores.clear()

        try:
            if self._ignore_list_file_handle:
                self._ignore_list_file_handle.seek(0)
                for line in self._ignore_list_file_handle:
                    entry = IgnoreFileEntry(line)

                    if entry.is_valid() and \
                       str( pathlib.Path(entry.get_file_name()).as_posix() ) == \
                       str(pathlib.Path(file_name).as_posix()):
                        rule_name = entry.get_rule_name()
                        if rule_name not in self._rule_ignores:
                            self._rule_ignores[rule_name] = []

                        self._rule_ignores[rule_name].append(IgnoreEntry(entry.get_hash(),
                                                                         entry.get_line_num(),
                                                                         entry.get_line_num()))

        except Exception as exc:  #pylint: disable=broad-except
            print("Failure while checking ignore list. Run with verbose mode for more information.")
            self.print_verbose("Exception on parsing ignore list: " + str(exc))
            self.print_verbose(traceback.format_exc())

    def disable(self, rule_name:str, line_num:int):
        if rule_name not in self._rule_ignores:
            self._rule_ignores[rule_name] = []

        self._rule_ignores[rule_name].append(IgnoreEntry('*', line_num, line_num))

    def is_filtered(self, rule_name:str, line_num:int, line_hash:hashlib.md5) -> bool:
        """ Returns True if the violation should not be logged """

        if '*' in self._rule_ignores:
            for ignore in self._rule_ignores['*']:
                if ignore.is_active():
                    if ignore.get_first() <= line_num <= ignore.get_last():
                        if ignore.get_hash() == '*' or ignore.get_hash() == str(line_hash):
                            ignore.mark_use()
                            return True

        if rule_name in self._rule_ignores:
            for ignore in self._rule_ignores[rule_name]:
                if ignore.is_active():
                    if ignore.get_first() <= line_num <= ignore.get_last():
                        if ignore.get_hash() == '*' or ignore.get_hash() == str(line_hash):
                            ignore.mark_use()
                            return True
        return False

class IgnoreFileEntry:
    """ Parses a line (string) into the members of an ignore entry from an ignore file.
        Always check is_valid() before using any of the getters on the object.
    """
    def __init__(self, line:str):
        self._valid = False
        self._line_num = -1
        self._col_num = -1
        self._hash = "NOHASH"

        parts = line.split(sep=': ')

        if len(parts) < 4:
            return

        # First value on line must be hash
        hash_part = parts[0].strip()
        if len(hash_part) == 32 and all(c in string.hexdigits for c in hash_part):
            self._hash = hash_part
        else:
            return

        # Second value on line must be the filename with optional line and col information
        file_info = parts[1]
        file_info_parts = file_info.rsplit(':',2)
        self._set_file_info(file_info_parts)

        if not self._set_log_type(parts[2]):
            return

        self._rule_name = parts[3]

        if len(parts) - 1 == 4:
            self._message = parts[4]
        else:
            self._message = ': '.join(parts[4:])

        self._valid = True

    def _set_file_info(self, file_info_parts) -> bool:
        if len(file_info_parts) >= 3:
            if file_info_parts[1].isdigit():
                if file_info_parts[2].isdigit():
                    self._col_num = int(file_info_parts[2])
                    self._line_num = int(file_info_parts[1])
                    self._file_name = file_info_parts[0]
            elif file_info_parts[2].isdigit():
                self._line_num = int(file_info_parts[2])
                self._file_name = file_info_parts[0] + ":" + file_info_parts[1]
            else:
                self._file_name = file_info_parts[0] + ":" + file_info_parts[1] + ":" + \
                                  file_info_parts[2]
        elif len(file_info_parts) == 2:
            if file_info_parts[1].isdigit():
                self._line_num = int(file_info_parts[1])
                self._file_name = file_info_parts[0]
            else:
                self._file_name = file_info_parts[0] + ":" + file_info_parts[1]
        else:
            self._file_name = file_info_parts[0]

        return True

    def _set_log_type(self, part:str) -> bool:
        if part == "ERROR":
            self._log_type = LogType.ERROR
            return True
        if part == "WARNING":
            self._log_type = LogType.WARNING
            return True

        return False

    def print(self):
        """Print string representation of the ignore file entry."""
        print("h: " + self.get_hash() + " f: " + self.get_file_name()
              + " l,c: "
              + str(self.get_line_num()) + ","
              + str(self.get_col_num()) + " t: "
              + str(self.get_log_level()) + " r: "
              + self.get_rule_name()
              + " m: " + self.get_message())

    def get_hash(self) -> str:
        return self._hash

    def get_file_name(self):
        return self._file_name

    def get_line_num(self) -> int:
        return self._line_num

    def get_col_num(self):
        return self._col_num

    def get_rule_name(self):
        return self._rule_name

    def get_log_level(self):
        return self._log_type

    def get_message(self):
        return self._message

    def is_valid(self) -> bool:
        return self._valid

class IgnoreEntry:
    """ IgnoreEntries are like ranges, except that:
        * The end value is inclusive, and thus called 'last'
        * The last value can be 'Inf' for infinite
        * They hold a hash value

        Also, the start value is referred to as start.

        The various comparison operators are overridden in ways that support the use of
        IgnoreEntries for the purpose of disabling logging of rules over certain line ranges.
        Their operation may not be directly intuitive.
    """
    def __init__(self, line_hash:str, first, last):
        self._first = Decimal(first)
        self._last = Decimal(last)
        self._hash = line_hash
        self._is_active = True


    def get_first(self) -> Decimal:
        return self._first

    def get_last(self) -> Decimal:
        return self._last

    def get_hash(self) -> str:
        return self._hash

    def is_active(self) -> bool:
        return self._is_active

    def mark_use(self):
        if self.get_hash() != '*':
            self._is_active = False

    def __lt__(self, key):
        """ Compare is done against the first value of the set only. """
        if isinstance(key, IgnoreEntry):
            return self.get_first() < key.get_first()
        return self.get_first() < key

    def __le__(self, key):
        """ Compare is done against the first value of the set only. """
        if isinstance(key, IgnoreEntry):
            return self.get_first() <= key.get_first()
        return self.get_first() <= key

    def __gt__(self, key):
        """ Compare is done against the first value of the set only. """
        if isinstance(key, IgnoreEntry):
            return self.get_first() > key.get_first()
        return self.get_first() > key

    def __ge__(self, key):
        """ Compare is done against the first value of the set only. """
        if isinstance(key, IgnoreEntry):
            return self.get_first() >= key.get_first()
        return self.get_first() >= key

    def __eq__(self, key):
        """ To be equal, the first, last, and hash value must all be equal """
        if isinstance(key, IgnoreEntry):
            return self.get_first() == key.get_first() and self.get_last() == key.get_last() and \
                self.get_hash() == key.get_hash()
        return False

    def __ne__(self, key):
        return not self.__eq__(key)
