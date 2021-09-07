import pytest
from io import StringIO
from rulecheck.ignore import IgnoreFile
from rulecheck.rule import LogType

#pylint: disable=line-too-long
#pylint: disable=redefined-outer-name

@pytest.fixture
def basic_ignore_file():
    """Creates handle to in-memory file-like object containing
       containing the four valid ignore entries"""
    content = """ff43cc7a3fc193bfefe7882f57931c2c: ./tests/src/basic utils/main.c: WARNING: rulepack1.printFilename: Visited file: ./tests/src/basic utils/main.c
52e1122bad199393fb129881e95fba54: ./tests/src/network/err.c: WARNING: rulepack1.printFilename: Visited file: ./tests/src/network/err.c
a1dd0f8b6a25c23d16733f52fc47835a: ./tests/src/network/err.c:12:9: ERROR: rulepack1.printRowsWithWord: use of the word not :     /* Will not exit. Uses errno. */
3f157419596186f3d6e2b2bec4d13d61: ./tests/src/network/err.c:13:9: ERROR: rulepack1.printRowsWithWord: use of the word not :     /* Will not exit. Does not use errno. */"""

    filehandle = StringIO()
    filehandle.write(content)
    return (content, filehandle)

@pytest.fixture
def bad_hash_file():
    """Creates handle to in-memory file-like object containing
       containing 3 valid ignore entries and one invalid one.
       The invalid entry is the 2nd in the list and it has an
       invalid hash with the string 'BADHASH' at the end of the
       hash value."""
    content = """ff43cc7a3fc193bfefe7882f57931c2c: ./tests/src/basic utils/main.c: WARNING: rulepack1.printFilename: Visited file: ./tests/src/basic utils/main.c
52e1122bad199393fb129881e95fba54BADHASH: ./tests/src/network/err.c: WARNING: rulepack1.printFilename: Visited file: ./tests/src/network/err.c
a1dd0f8b6a25c23d16733f52fc47835a: ./tests/src/network/err.c:12:9: ERROR: rulepack1.printRowsWithWord: use of the word not :     /* Will not exit. Uses errno. */
3f157419596186f3d6e2b2bec4d13d61: ./tests/src/network/err.c:13:9: ERROR: rulepack1.printRowsWithWord: use of the word not :     /* Will not exit. Does not use errno. */"""

    filehandle = StringIO()
    filehandle.write(content)
    return (content, filehandle)

def test_file_load(basic_ignore_file, capsys):  #pylint: disable=redefined-outer-name
    """ Test basic loading from file handle, and printing to console of loaded contents """
    ignorefile = IgnoreFile()

    ignorefile.set_file_handle(basic_ignore_file[1])

    ignorefile.load()

    ignorefile.print_to_console()

    captured = capsys.readouterr()

    assert basic_ignore_file[0] in captured.out

def test_file_load_with_invalid_entry(bad_hash_file, capsys):
    """ Test that bad entries are not loaded """
    ignorefile = IgnoreFile()

    ignorefile.set_file_handle(bad_hash_file[1])

    ignorefile.load()

    ignorefile.print_to_console()

    captured = capsys.readouterr()

    assert not 'BADHASH' in captured.out


def test_get_ignores_of_file(basic_ignore_file):  #pylint: disable=too-many-statements
    """ Test get_ignores_of_file function """
    ignorefile = IgnoreFile()

    ignorefile.set_file_handle(basic_ignore_file[1])

    ignorefile.load()

    assert len(ignorefile.get_ignores_of_file('nosuchfile')) == 0

    entries_of_main_c = ignorefile.get_ignores_of_file('./tests/src/basic utils/main.c')
    assert len(entries_of_main_c) == 1

    assert entries_of_main_c[0].get_rule_name() == 'rulepack1.printFilename'
    assert entries_of_main_c[0].get_file_name() == './tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_first() == -1
    assert entries_of_main_c[0].get_last() == -1
    assert entries_of_main_c[0].get_line_num() == -1
    assert entries_of_main_c[0].get_col_num() == -1
    assert entries_of_main_c[0].get_log_type() == LogType.WARNING
    assert entries_of_main_c[0].get_message() == 'Visited file: ./tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_hash() == 'ff43cc7a3fc193bfefe7882f57931c2c'
    assert entries_of_main_c[0].is_active()
    assert entries_of_main_c[0].is_valid()

    entries_of_err_c = ignorefile.get_ignores_of_file('./tests/src/network/err.c')
    assert len(entries_of_err_c) == 3

    assert entries_of_err_c[0].get_rule_name() == 'rulepack1.printFilename'
    assert entries_of_err_c[0].get_file_name() == './tests/src/network/err.c'
    assert entries_of_err_c[0].get_first() == -1
    assert entries_of_err_c[0].get_last() == -1
    assert entries_of_err_c[0].get_line_num() == -1
    assert entries_of_err_c[0].get_col_num() == -1
    assert entries_of_err_c[0].get_log_type() == LogType.WARNING
    assert entries_of_err_c[0].get_message() == 'Visited file: ./tests/src/network/err.c'
    assert entries_of_err_c[0].get_hash() == '52e1122bad199393fb129881e95fba54'
    assert entries_of_err_c[0].is_active()
    assert entries_of_err_c[0].is_valid()

    assert entries_of_err_c[1].get_rule_name() == 'rulepack1.printRowsWithWord'
    assert entries_of_err_c[1].get_file_name() == './tests/src/network/err.c'
    assert entries_of_err_c[1].get_first() == 12
    assert entries_of_err_c[1].get_last() == 12
    assert entries_of_err_c[1].get_line_num() == 12
    assert entries_of_err_c[1].get_col_num() == 9
    assert entries_of_err_c[1].get_log_type() == LogType.ERROR
    assert entries_of_err_c[1].get_message() == 'use of the word not :     /* Will not exit. Uses errno. */'
    assert entries_of_err_c[1].get_hash() == 'a1dd0f8b6a25c23d16733f52fc47835a'
    assert entries_of_err_c[1].is_active()
    assert entries_of_err_c[1].is_valid()

    assert entries_of_err_c[2].get_rule_name() == 'rulepack1.printRowsWithWord'
    assert entries_of_err_c[2].get_file_name() == './tests/src/network/err.c'
    assert entries_of_err_c[2].get_first() == 13
    assert entries_of_err_c[2].get_last() == 13
    assert entries_of_err_c[2].get_line_num() == 13
    assert entries_of_err_c[2].get_col_num() == 9
    assert entries_of_err_c[2].get_log_type() == LogType.ERROR
    assert entries_of_err_c[2].get_message() == 'use of the word not :     /* Will not exit. Does not use errno. */'
    assert entries_of_err_c[2].get_hash() == '3f157419596186f3d6e2b2bec4d13d61'
    assert entries_of_err_c[2].is_active()
    assert entries_of_err_c[2].is_valid()

def test_add_before_load(basic_ignore_file):
    """Test adding entry before a load from file."""

    ignorefile = IgnoreFile()
    ignorefile.set_file_handle(basic_ignore_file[1])

    ignorefile.add('1234567890abcdef1234567890abcdef',
                   'ERROR', 100, 20, 'never do this',
                   './tests/src/basic utils/main.c',
                   'customRule')

    entries_of_main_c = ignorefile.get_ignores_of_file('./tests/src/basic utils/main.c')
    assert len(entries_of_main_c) == 1

    assert entries_of_main_c[0].get_rule_name() == 'customRule'
    assert entries_of_main_c[0].get_file_name() == './tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_first() == 100
    assert entries_of_main_c[0].get_last() == 100
    assert entries_of_main_c[0].get_line_num() == 100
    assert entries_of_main_c[0].get_col_num() == 20
    assert entries_of_main_c[0].get_log_type() == LogType.ERROR
    assert entries_of_main_c[0].get_message() == 'never do this'
    assert entries_of_main_c[0].get_hash() == '1234567890abcdef1234567890abcdef'
    assert entries_of_main_c[0].is_active()
    assert entries_of_main_c[0].is_valid()

    ignorefile.load()

    entries_of_main_c = ignorefile.get_ignores_of_file('./tests/src/basic utils/main.c')
    assert len(entries_of_main_c) == 1

    assert entries_of_main_c[0].get_rule_name() == 'rulepack1.printFilename'
    assert entries_of_main_c[0].get_file_name() == './tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_first() == -1
    assert entries_of_main_c[0].get_last() == -1
    assert entries_of_main_c[0].get_line_num() == -1
    assert entries_of_main_c[0].get_col_num() == -1
    assert entries_of_main_c[0].get_log_type() == LogType.WARNING
    assert entries_of_main_c[0].get_message() == 'Visited file: ./tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_hash() == 'ff43cc7a3fc193bfefe7882f57931c2c'
    assert entries_of_main_c[0].is_active()
    assert entries_of_main_c[0].is_valid()

    # Quick sanity check that other ignores loaded:
    entries_of_err_c = ignorefile.get_ignores_of_file('./tests/src/network/err.c')
    assert len(entries_of_err_c) == 3


def test_add_after_load(basic_ignore_file):
    """Test adding entry after a load from file."""

    ignorefile = IgnoreFile()
    ignorefile.set_file_handle(basic_ignore_file[1])

    ignorefile.load()

    ignorefile.add('1234567890abcdef1234567890abcdef',
                   'ERROR', 100, 20, 'never do this',
                   './tests/src/basic utils/main.c',
                   'customRule')

    entries_of_main_c = ignorefile.get_ignores_of_file('./tests/src/basic utils/main.c')
    assert len(entries_of_main_c) == 2

    assert entries_of_main_c[0].get_rule_name() == 'rulepack1.printFilename'
    assert entries_of_main_c[0].get_file_name() == './tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_first() == -1
    assert entries_of_main_c[0].get_last() == -1
    assert entries_of_main_c[0].get_line_num() == -1
    assert entries_of_main_c[0].get_col_num() == -1
    assert entries_of_main_c[0].get_log_type() == LogType.WARNING
    assert entries_of_main_c[0].get_message() == 'Visited file: ./tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_hash() == 'ff43cc7a3fc193bfefe7882f57931c2c'
    assert entries_of_main_c[0].is_active()
    assert entries_of_main_c[0].is_valid()

    assert entries_of_main_c[1].get_rule_name() == 'customRule'
    assert entries_of_main_c[1].get_file_name() == './tests/src/basic utils/main.c'
    assert entries_of_main_c[1].get_first() == 100
    assert entries_of_main_c[1].get_last() == 100
    assert entries_of_main_c[1].get_line_num() == 100
    assert entries_of_main_c[1].get_col_num() == 20
    assert entries_of_main_c[1].get_log_type() == LogType.ERROR
    assert entries_of_main_c[1].get_message() == 'never do this'
    assert entries_of_main_c[1].get_hash() == '1234567890abcdef1234567890abcdef'
    assert entries_of_main_c[1].is_active()
    assert entries_of_main_c[1].is_valid()

    # Quick sanity check that other ignores loaded:
    entries_of_err_c = ignorefile.get_ignores_of_file('./tests/src/network/err.c')
    assert len(entries_of_err_c) == 3

def test_bump(basic_ignore_file):  #pylint: disable=too-many-statements
    """Test that bump will bump all appropriate entries."""
    ignorefile = IgnoreFile()
    ignorefile.set_file_handle(basic_ignore_file[1])
    ignorefile.load()

    # Add additional entry so bump is expected to bump 2 entries in total.
    ignorefile.add('1234567890abcdef1234567890abcdef',
                   'ERROR', 100, 20, 'never do this',
                   './tests/src/network/err.c',
                   'customRule')

    ignorefile.bump('./tests/src/network/err.c', 13, 1000)

    entries_of_main_c = ignorefile.get_ignores_of_file('./tests/src/basic utils/main.c')
    assert len(entries_of_main_c) == 1

    assert entries_of_main_c[0].get_rule_name() == 'rulepack1.printFilename'
    assert entries_of_main_c[0].get_file_name() == './tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_first() == -1
    assert entries_of_main_c[0].get_last() == -1
    assert entries_of_main_c[0].get_line_num() == -1
    assert entries_of_main_c[0].get_col_num() == -1
    assert entries_of_main_c[0].get_log_type() == LogType.WARNING
    assert entries_of_main_c[0].get_message() == 'Visited file: ./tests/src/basic utils/main.c'
    assert entries_of_main_c[0].get_hash() == 'ff43cc7a3fc193bfefe7882f57931c2c'
    assert entries_of_main_c[0].is_active()
    assert entries_of_main_c[0].is_valid()

    entries_of_err_c = ignorefile.get_ignores_of_file('./tests/src/network/err.c')
    assert len(entries_of_err_c) == 4

    assert entries_of_err_c[0].get_rule_name() == 'rulepack1.printFilename'
    assert entries_of_err_c[0].get_file_name() == './tests/src/network/err.c'
    assert entries_of_err_c[0].get_first() == -1
    assert entries_of_err_c[0].get_last() == -1
    assert entries_of_err_c[0].get_line_num() == -1
    assert entries_of_err_c[0].get_col_num() == -1
    assert entries_of_err_c[0].get_log_type() == LogType.WARNING
    assert entries_of_err_c[0].get_message() == 'Visited file: ./tests/src/network/err.c'
    assert entries_of_err_c[0].get_hash() == '52e1122bad199393fb129881e95fba54'
    assert entries_of_err_c[0].is_active()
    assert entries_of_err_c[0].is_valid()

    assert entries_of_err_c[1].get_rule_name() == 'rulepack1.printRowsWithWord'
    assert entries_of_err_c[1].get_file_name() == './tests/src/network/err.c'
    assert entries_of_err_c[1].get_first() == 12
    assert entries_of_err_c[1].get_last() == 12
    assert entries_of_err_c[1].get_line_num() == 12
    assert entries_of_err_c[1].get_col_num() == 9
    assert entries_of_err_c[1].get_log_type() == LogType.ERROR
    assert entries_of_err_c[1].get_message() == 'use of the word not :     /* Will not exit. Uses errno. */'
    assert entries_of_err_c[1].get_hash() == 'a1dd0f8b6a25c23d16733f52fc47835a'
    assert entries_of_err_c[1].is_active()
    assert entries_of_err_c[1].is_valid()

    assert entries_of_err_c[2].get_rule_name() == 'rulepack1.printRowsWithWord'
    assert entries_of_err_c[2].get_file_name() == './tests/src/network/err.c'
    assert entries_of_err_c[2].get_first() == 1013
    assert entries_of_err_c[2].get_last() == 1013
    assert entries_of_err_c[2].get_line_num() == 1013
    assert entries_of_err_c[2].get_col_num() == 9
    assert entries_of_err_c[2].get_log_type() == LogType.ERROR
    assert entries_of_err_c[2].get_message() == 'use of the word not :     /* Will not exit. Does not use errno. */'
    assert entries_of_err_c[2].get_hash() == '3f157419596186f3d6e2b2bec4d13d61'
    assert entries_of_err_c[2].is_active()
    assert entries_of_err_c[2].is_valid()

    assert entries_of_err_c[3].get_rule_name() == 'customRule'
    assert entries_of_err_c[3].get_file_name() == './tests/src/network/err.c'
    assert entries_of_err_c[3].get_first() == 1100
    assert entries_of_err_c[3].get_last() == 1100
    assert entries_of_err_c[3].get_line_num() == 1100
    assert entries_of_err_c[3].get_col_num() == 20
    assert entries_of_err_c[3].get_log_type() == LogType.ERROR
    assert entries_of_err_c[3].get_message() == 'never do this'
    assert entries_of_err_c[3].get_hash() == '1234567890abcdef1234567890abcdef'
    assert entries_of_err_c[3].is_active()
    assert entries_of_err_c[3].is_valid()


def test_write():
    """Confirm write will write all ignore entries to file, but leaves entries in memory."""
    ignorefile = IgnoreFile()
    filehandle = StringIO()
    ignorefile.set_file_handle(filehandle)

    # Add three entries
    ignorefile.add('1234567890abcdef1234567890abcdef',
                   'ERROR', 100, 20, 'never do this',
                   './tests/src/network/err.c',
                   'customRule1')
    ignorefile.add('a234567890abcdef1234567890abcdef',
                   'WARNING', 105, -1, 'never do this 2',
                   './tests/src/network/err.c',
                   'customRule2')
    ignorefile.add('b234567890abcdef1234567890abcdef',
                   'ERROR', 100, 20, 'never do this',
                   './tests/src/main.c',
                   'customRule1')

    ignorefile.write()

    filehandle.seek(0,0)

    expectedcontent1 = '1234567890abcdef1234567890abcdef: ./tests/src/network/err.c:100:20: ERROR: customRule1: never do this'
    expectedcontent2 = 'a234567890abcdef1234567890abcdef: ./tests/src/network/err.c:105: WARNING: customRule2: never do this 2'
    expectedcontent3 = 'b234567890abcdef1234567890abcdef: ./tests/src/main.c:100:20: ERROR: customRule1: never do this'

    actualcontent = filehandle.read()

    assert expectedcontent1 in actualcontent
    assert expectedcontent2 in actualcontent
    assert expectedcontent3 in actualcontent

    assert len(ignorefile.get_ignores_of_file('./tests/src/network/err.c')) == 2
    assert len(ignorefile.get_ignores_of_file('./tests/src/main.c')) == 1

def test_flush():
    """Confirm flush will write all ignore entries to file and remove them from memory."""
    ignorefile = IgnoreFile()
    filehandle = StringIO()
    ignorefile.set_file_handle(filehandle)

    # Add three entries
    ignorefile.add('1234567890abcdef1234567890abcdef',
                   'ERROR', 100, 20, 'never do this',
                   './tests/src/network/err.c',
                   'customRule1')
    ignorefile.add('a234567890abcdef1234567890abcdef',
                   'WARNING', 105, -1, 'never do this 2',
                   './tests/src/network/err.c',
                   'customRule2')
    ignorefile.add('b234567890abcdef1234567890abcdef',
                   'ERROR', 100, 20, 'never do this',
                   './tests/src/main.c',
                   'customRule1')

    ignorefile.flush()

    filehandle.seek(0,0)

    expectedcontent1 = '1234567890abcdef1234567890abcdef: ./tests/src/network/err.c:100:20: ERROR: customRule1: never do this'
    expectedcontent2 = 'a234567890abcdef1234567890abcdef: ./tests/src/network/err.c:105: WARNING: customRule2: never do this 2'
    expectedcontent3 = 'b234567890abcdef1234567890abcdef: ./tests/src/main.c:100:20: ERROR: customRule1: never do this'

    actualcontent = filehandle.read()

    assert expectedcontent1 in actualcontent
    assert expectedcontent2 in actualcontent
    assert expectedcontent3 in actualcontent

    assert len(ignorefile.get_ignores_of_file('./tests/src/network/err.c')) == 0
    assert len(ignorefile.get_ignores_of_file('./tests/src/main.c')) == 0
