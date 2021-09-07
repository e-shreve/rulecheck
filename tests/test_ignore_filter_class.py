import pytest
from io import StringIO
from rulecheck.ignore import IgnoreFile
from rulecheck.ignore import IgnoreFilter
from rulecheck.rule import LogType

#pylint: disable=line-too-long

@pytest.fixture
def basic_ignore_file_obj():
    """Creates IgnoreFile containing four valid ignore entries"""
    content = """ff43cc7a3fc193bfefe7882f57931c2c: ./tests/src/basic utils/main.c: WARNING: rulepack1.printFilename: Visited file: ./tests/src/basic utils/main.c
52e1122bad199393fb129881e95fba54: ./tests/src/network/err.c: WARNING: rulepack1.printFilename: Visited file: ./tests/src/network/err.c
a1dd0f8b6a25c23d16733f52fc47835a: ./tests/src/network/err.c:12:9: ERROR: rulepack1.printRowsWithWord: use of the word not :     /* Will not exit. Uses errno. */
3f157419596186f3d6e2b2bec4d13d61: ./tests/src/network/err.c:13:9: ERROR: rulepack1.printRowsWithWord: use of the word not :     /* Will not exit. Does not use errno. */"""

    filehandle = StringIO()
    filehandle.write(content)

    ignore_file = IgnoreFile()
    ignore_file.set_file_handle(filehandle)
    ignore_file.load()

    return ignore_file

def test_confirm_ignores_enabled_on_init_filter(basic_ignore_file_obj):
    ignore_filter = IgnoreFilter(basic_ignore_file_obj)
    ignore_filter.init_filter('./tests/src/network/err.c')

    # printFilename rule entry has no line number so use -1 for line num
    assert ignore_filter.is_filtered('rulepack1.printFilename', -1, '52e1122bad199393fb129881e95fba54')

    # printRowsWithWord entries do have line numbers.
    assert ignore_filter.is_filtered('rulepack1.printRowsWithWord', 12, 'a1dd0f8b6a25c23d16733f52fc47835a')
    assert ignore_filter.is_filtered('rulepack1.printRowsWithWord', 13, '3f157419596186f3d6e2b2bec4d13d61')


def test_confirm_non_existent_ignores_are_not_filtered(basic_ignore_file_obj):
    ignore_filter = IgnoreFilter(basic_ignore_file_obj)
    ignore_filter.init_filter('./tests/src/network/err.c')

    # Line number does not match any ignore entry
    assert not ignore_filter.is_filtered('rulepack1.printRowsWithWord', 22, '*')

    # Hash does not match any ignore entry
    assert not ignore_filter.is_filtered('rulepack1.printRowsWithWord', 12, '12345678901234567890123456789023')

    # Rulename does not match any ignore entry
    assert not ignore_filter.is_filtered('rulepack1.printDOESNOTEXIST', 12, 'a1dd0f8b6a25c23d16733f52fc47835a')

def test_confirm_ignore_entry_with_hash_filtered_only_once(basic_ignore_file_obj):
    ignore_filter = IgnoreFilter(basic_ignore_file_obj)
    ignore_filter.init_filter('./tests/src/network/err.c')

    assert ignore_filter.is_filtered('rulepack1.printFilename', -1, '52e1122bad199393fb129881e95fba54')
    assert not ignore_filter.is_filtered('rulepack1.printFilename', -1, '52e1122bad199393fb129881e95fba54')
    assert not ignore_filter.is_filtered('rulepack1.printFilename', -1, '52e1122bad199393fb129881e95fba54')

def test_disable(basic_ignore_file_obj):
    ignore_filter = IgnoreFilter(basic_ignore_file_obj)
    ignore_filter.init_filter('./tests/src/network/err.c')

    ignore_filter.disable('disabledrule', 1000)

    # Show that rule is disabled regardless of hash value
    assert ignore_filter.is_filtered('disabledrule', 1000, '52e1122bad199393fb129881e95fba54')
    assert ignore_filter.is_filtered('disabledrule', 1000, '88e1122bad199393fb129881e95fba54')
    assert ignore_filter.is_filtered('disabledrule', 1000, '*')

    # Show that rule is filtered repeatedly for same line and hash
    assert ignore_filter.is_filtered('disabledrule', 1000, '99e1122bad199393fb129881e95fba54')
    assert ignore_filter.is_filtered('disabledrule', 1000, '99e1122bad199393fb129881e95fba54')

    # Show that rule is not filtered on a differetn line
    assert not ignore_filter.is_filtered('disabledrule', 1001, '99e1122bad199393fb129881e95fba54')
    assert not ignore_filter.is_filtered('disabledrule', 999, '99e1122bad199393fb129881e95fba54')
