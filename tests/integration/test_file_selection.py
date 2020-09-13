import pytest

def testsquare(capsys):
    num = 7
    print(num)
    assert num*num == 49

    captured = capsys.readouterr()
    assert "7" in captured.out
