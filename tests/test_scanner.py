from even_more_itertools import Scanner


def test_scanner_empty():
    stream = []
    scanner = Scanner(stream)
    assert list(scanner.scan_until(lambda s: isinstance(s, int))) == []
    assert list(scanner.scan_while(lambda s: isinstance(s, int))) == []


def test_scanner_single_pred():
    bigger_than_3 = lambda i: i > 3

    stream = range(8)
    scanner = Scanner(stream)
    assert list(scanner.scan_until(bigger_than_3)) == [0, 1, 2, 3]
    assert list(scanner.scan_until(bigger_than_3)) == []
    assert list(scanner.scan_while(bigger_than_3)) == [4, 5, 6, 7]


def test_scanner_multiple_preds():
    is_int = lambda o: isinstance(o, int)
    is_dot = lambda s: s == '.'

    stream = ['a', 0, 'b', 1, 2, 'c', 'd', 3, 4, '.']
    scanner = Scanner(stream)
    scanner.skip_until(is_int)
    scanner.skip_while(is_int)
    scanner.skip_until(is_int)
    assert list(scanner.scan_while(is_int)) == [1, 2]
    scanner.skip_until(is_dot)
    assert list(scanner.scan_while(is_dot)) == ['.']


def test_scanner_remainder():
    bigger_than_3 = lambda i: i > 3

    stream = range(8)
    scanner = Scanner(stream)
    assert list(scanner.scan_until(bigger_than_3)) == [0, 1, 2, 3]
    assert list(scanner) == [4, 5, 6, 7]  # consume remainder


def test_scanner_mix_and_match_next():
    bigger_than_3 = lambda i: i > 3

    stream = range(8)
    scanner = Scanner(stream)
    assert list(scanner.scan_until(bigger_than_3)) == [0, 1, 2, 3]
    assert next(scanner) == 4
    assert next(scanner) == 5
    assert list(scanner.scan_while(bigger_than_3)) == [6, 7]
