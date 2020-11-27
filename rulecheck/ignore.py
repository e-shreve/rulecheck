from decimal import Decimal
import glob
import hashlib
import pathlib
import string
import traceback
import typing
from typing import List

# Local imports
from rulecheck.python_patch.patch import fromfile as patch_from_file
from rulecheck.rule import LogType


#pylint: disable=missing-function-docstring
#pylint: disable=too-many-arguments
#pylint: disable=too-many-instance-attributes

def get_ignore_hash(file_name:str,
                    source_line:str, use_leading_whitespace:bool,
                    log_type_name:str,
                    rule_name:str):
    """ Generates the ignore hash for the given inputs. """

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

class IgnoreEntry:
    """ IgnoreEntries hold all parts of an Ignore Entry and can be compared like ranges,
        except that:
        * The end value is inclusive, and thus called 'last'
        * The last value can be 'Inf' for infinite
        * They hold a hash value

        Also, the start value is referred to as start.

        The various comparison operators are overridden in ways that support the use of
        IgnoreEntries for the purpose of disabling logging of rules over certain line ranges.
        Their operation may not be directly intuitive.
    """
    def __init__(self, rule_name:str, line_hash:str, first, last):
        self._rule_name = rule_name
        self._first = Decimal(first)
        self._last = Decimal(last)
        self._col_num = Decimal(-1)
        self._hash = line_hash
        self._is_active = True
        self._file_name = "*" # Filename is optional
        self._log_type = LogType.ERROR
        self._message = ""
        self._is_valid = True

    @staticmethod
    def _invalid_ignore_entry() -> 'IgnoreEntry':
        entry = IgnoreEntry("", "", 0, 0)
        entry._is_valid = False  #pylint: disable=protected-access
        return entry

    @staticmethod
    def from_ignore_file_line(ignore_file_line:str) -> 'IgnoreEntry':
        parts = ignore_file_line.split(sep=': ')

        if len(parts) < 4:
            return IgnoreEntry._invalid_ignore_entry()

        # First value on line must be hash
        hash_part = parts[0].strip()
        if len(hash_part) == 32 and all(c in string.hexdigits for c in hash_part):
            ignore_hash = hash_part
        else:
            return IgnoreEntry._invalid_ignore_entry()

        # Second value on line must be the filename with optional line and col information
        file_info = parts[1]
        file_info_parts = file_info.rsplit(':',2)
        (file_name, line_no, col_no) = IgnoreEntry._get_file_info(file_info_parts) # @UnusedVariable

        logstring = parts[2]
        if not IgnoreEntry._is_valid_log_type(logstring):
            return IgnoreEntry._invalid_ignore_entry()

        rule_name = parts[3]

        message = parts[4]
        if not len(parts) - 1 == 4:
            message = ': '.join(parts[4:])

        entry = IgnoreEntry(rule_name, ignore_hash, line_no, line_no)
        entry._set_col_num(col_no)       #pylint: disable=protected-access
        entry._set_file_name(file_name)  #pylint: disable=protected-access
        entry._set_log_type(logstring)   #pylint: disable=protected-access
        entry._set_message(message)      #pylint: disable=protected-access

        return entry

    @staticmethod
    def _get_file_info(file_info_parts) -> (str, int, int):
        file_name = ""
        line_num = -1
        col_num = -1

        if len(file_info_parts) >= 3:
            if file_info_parts[1].isdigit():
                if file_info_parts[2].isdigit():
                    col_num = int(file_info_parts[2])
                    line_num = int(file_info_parts[1])
                    file_name = file_info_parts[0]
            elif file_info_parts[2].isdigit():
                line_num = int(file_info_parts[2])
                file_name = file_info_parts[0] + ":" + file_info_parts[1]
            else:
                file_name = file_info_parts[0] + ":" + file_info_parts[1] + ":" + \
                                  file_info_parts[2]
        elif len(file_info_parts) == 2:
            if file_info_parts[1].isdigit():
                line_num = int(file_info_parts[1])
                file_name = file_info_parts[0]
            else:
                file_name = file_info_parts[0] + ":" + file_info_parts[1]
        else:
            file_name = file_info_parts[0]

        return (file_name, line_num, col_num)

    @staticmethod
    def _is_valid_log_type(part:str) -> bool:
        if part == "ERROR":
            return True
        if part == "WARNING":
            return True

        return False

    def _set_log_type(self, part:str) -> bool:
        if part == "ERROR":
            self._log_type = LogType.ERROR
            return True
        if part == "WARNING":
            self._log_type = LogType.WARNING
            return True

        return False

    def _set_file_name(self, file_name:str):
        self._file_name = file_name

    def _set_col_num(self, col_num:int):
        self._col_num = Decimal(col_num)

    def _set_line_num(self, line_num:int):
        self._first= Decimal(line_num)
        self._last= Decimal(line_num)

    def _set_message(self, message:str):
        self._message = message

    def get_rule_name(self) -> str:
        return self._rule_name

    def get_file_name(self):
        return self._file_name

    def get_first(self) -> Decimal:
        return self._first

    def get_last(self) -> Decimal:
        return self._last

    def get_line_num(self) -> Decimal:
        return self._first

    def get_col_num(self) -> Decimal:
        return self._col_num

    def get_log_type(self) -> LogType:
        return self._log_type

    def get_message(self) -> str:
        return self._message

    def get_hash(self) -> str:
        return self._hash

    def is_active(self) -> bool:
        return self._is_active

    def is_valid(self) -> bool:
        return self._is_valid

    def mark_use(self):
        if self.get_hash() != '*':
            self._is_active = False

    def get_ignore_file_line(self) -> str:
        if not self.is_valid():
            return ""

        colstr = ""
        linestr = ""

        if self._first > -1:
            linestr = str(self._first)

        if self._col_num > -1:
            colstr = str(self._col_num)

        location = ':'.join(filter(None, [self._file_name, linestr, colstr]))

        return ': '.join(filter(None, [self._hash, location, self._log_type.name, self._rule_name,
                                       self._message]))

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
        """ Negation of __eq__(key) """
        return not self.__eq__(key)


class IgnoreFile:
    """ Used to manage (read, write, flush) Ignore File contents
    """

    def __init__(self, verbose:bool):
        self._file_ignores = {}
        self._suspect_ignores = {}
        self._verbose = verbose
        self._file_handle = None

    def print_verbose(self, message:str):
        if self._verbose:
            print(message)

    def set_file_handle(self, file_handle:typing.TextIO):
        self._file_handle = file_handle

    def load(self):
        self._file_ignores.clear()

        try:
            if self._file_handle:
                self._file_handle.seek(0)
                for line in self._file_handle:
                    entry = IgnoreEntry.from_ignore_file_line(line)

                    if entry and entry.is_valid():
                        file_name = pathlib.PurePath(entry.get_file_name()).as_posix()

                        if file_name not in self._file_ignores:
                            self._file_ignores[file_name] = []

                        self._file_ignores[file_name].append(entry)

        except Exception as exc:  #pylint: disable=broad-except
            print("Failure while checking ignore list. Run with verbose mode for more information.")
            self.print_verbose("Exception on parsing ignore list: " + str(exc))
            self.print_verbose(traceback.format_exc())

    def add(self, log_hash, log_type:str, line:int, col:int, msg:str,
            file_name:str, rule_name:str):

        entry = IgnoreEntry(rule_name, log_hash, line, line)
        entry._set_file_name(file_name)
        entry._set_log_type(log_type)
        entry._set_message(msg)
        entry._set_col_num(col)

        file_name_posix = pathlib.PurePath(entry.get_file_name()).as_posix()

        if file_name_posix not in self._file_ignores:
            self._file_ignores[file_name_posix] = []

        self._file_ignores[file_name_posix].append(entry)

    def get_ignores_of_file(self, file_name:str) -> List[IgnoreEntry]:
        file_name_posix = pathlib.PurePath(file_name).as_posix()
        if file_name_posix in self._file_ignores:
            return self._file_ignores[file_name_posix].copy()
        return []

    def bump(self, file_name:str, old_line:int, diff:int):
        if not file_name in self._file_ignores:
            file_name = "./"+ file_name

        if file_name in self._file_ignores:
            ignores = self._file_ignores[file_name]

            for ignore in ignores:
                curent_line_num = ignore.get_line_num()
                if curent_line_num >= old_line:
                    ignore._set_line_num(curent_line_num + diff) #pylint: disable=protected-access

    def print_to_console(self):
        for file_name in self._file_ignores:
            for ignore in self._file_ignores[file_name]:
                print(ignore.get_ignore_file_line(), end = "")

    def write(self):
        for file_name in self._file_ignores:
            for ignore in self._file_ignores[file_name]:
                self._file_handle.write(ignore.get_ignore_file_line() + "\n")

    def flush(self):
        self.write()
        self._file_ignores.clear()

class IgnoreFilter:
    """ Used to filter log messages.
        Handle to an open ignore list file is passed on object creation.
        Use init_filter to load all ignore entries from the file for a given source file.
    """

    def __init__(self, ignore_file:IgnoreFile, verbose:bool):
        self._ignore_file = ignore_file
        self._rule_ignores = {}
        self._verbose = verbose

    def print_verbose(self, message:str):
        if self._verbose:
            print(message)


    def init_filter(self, file_name:str):
        """ Loads all ignore rules from the ignore file for the given source file. """
        self._rule_ignores.clear()

        try:
            if self._ignore_file:
                ignores_of_file = self._ignore_file.get_ignores_of_file(file_name)

                # Store each ignore entry in a map keyed by rule name
                for entry in ignores_of_file:
                    rule_name = entry.get_rule_name()
                    if rule_name not in self._rule_ignores:
                        self._rule_ignores[rule_name] = []

                    self._rule_ignores[rule_name].append(entry)

        except Exception as exc:  #pylint: disable=broad-except
            print("Failure while checking ignore list. Run with verbose mode for more information.")
            self.print_verbose("Exception on parsing ignore list: " + str(exc))
            self.print_verbose(traceback.format_exc())

    def disable(self, rule_name:str, line_num:int):
        """ Disable a rule (ignore it) for the given line number. """
        if rule_name not in self._rule_ignores:
            self._rule_ignores[rule_name] = []

        # Use '*' for IgnoreEntry so any hash value will be ingored.
        self._rule_ignores[rule_name].append(IgnoreEntry(rule_name, '*', line_num, line_num))

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


VERBOSE_ENABLED: bool


def print_verbose(message:str):
    global VERBOSE_ENABLED
    if VERBOSE_ENABLED:
        print(message)

def print_patch(patch):
    print("patch: " + str(patch.source) + " " + str(patch.target) + " " + str(patch.type))
    for hunk in patch:
        print("  " + ' '.join([str(hunk.startsrc), str(hunk.linessrc),
                               str(hunk.starttgt), str(hunk.linestgt),
                               str(hunk.invalid), str(hunk.desc), str(hunk.text)]))

def process_patch(patch_file:str, ignores):
    patchset = patch_from_file(patch_file)
    for patch in patchset:
        for hunk in reversed(patch):
            ignores.bump(patch.source.decode("utf-8"), hunk.startsrc, hunk.linestgt - hunk.linessrc)


def process_patches(globs:[str], ignores):
    if (not globs is None) and len(globs) > 0:
        for glob_str in globs:
            for patch_path in glob.iglob(glob_str, recursive=True):
                process_patch(patch_path, ignores)

def ignorelist_update_command(args, verbose:bool) -> int:
    print(args.patch_ignore)

    # Open question: how to handle file renames in patch files? what does that look like?
    # patch library says that file renames dno't work "out of the box" What does that mean?


    global VERBOSE_ENABLED

    VERBOSE_ENABLED = verbose

    ignore_list_file_handle = None
    if args.ignorelist:
        print_verbose("Ignore list specified: " + args.ignorelist)
        ignore_list_file_handle = open(args.ignorelist, "r")

    ignores = IgnoreFile(VERBOSE_ENABLED)
    ignores.set_file_handle(ignore_list_file_handle)
    ignores.load()
    ignore_list_file_handle.close() #TODO use try finally to close

    ignores.print_to_console()

    ignore_list_file_handle.close()

    process_patches([item for sublist in args.patch_ignore for item in sublist], ignores)

    ignore_list_out = args.ignorelist
    if args.generateignorefile:
        ignore_list_out = args.generateignorefile

    ignore_list_file_handle = open(ignore_list_out, "w")
    ignores.set_file_handle(ignore_list_file_handle)
    ignores.write()
    ignore_list_file_handle.close() #TODO use try finally to close

    ignores.print_to_console()

    return 0
