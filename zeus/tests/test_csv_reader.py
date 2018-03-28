# -*- coding: utf-8 -*-

from zeus.utils import (CSVReader, get_encoding, CSVCellError,
                        pick_sample, get_dialect)
from unittest import TestCase, main
import pytest


class CSVReaderTests(TestCase):

    def test001_nodata(self):
        reader = CSVReader('')
        assert ValueError

    def test002_data(self):
        inp = ("testmail10testmail.com:testname0:testsurname0\n"
               "testmail1@testmail.com:δοκιμαστικόόνομα:δοκιμαστικόεπίθετο\n"
               "testmail2@testmail.com:όνομα3:επίθετο3\n")
        reader = CSVReader(inp)
        assert len(list(reader)) > 0

    def test003_readAllData(self):
        inp = ("testmail10testmail.com:testname0:testsurname0\n"
               "testmail1@testmail.com:δοκιμαστικόόνομα:δοκιμαστικόεπίθετο\n"
               "testmail2@testmail.com:όνομα3:επίθετο3\n")
        lines = 0
        for nl in inp:
            if nl == '\n':
                lines += 1
        reader = CSVReader(inp)
        assert len(list(reader)) == lines

    def test004_get_encoding(self):
        encodings = ['utf-8', 'iso8859-7', 'utf-16', 'utf-16le', 'utf-16be']
        unicode_string = 'Ένα test string for encoding detection purposes\n'
        encoded_strings = []
        for encoding in encodings:
            encoded_strings.append(unicode_string.encode(encoding))
        encodings_detected = []
        for enc_string in encoded_strings:
            encodings_detected.append(get_encoding(enc_string, encodings=encodings))
        assert encodings == encodings_detected

    def test005_cells_less_than_min_fields(self):
        inp = ("testmail10testmail.com:testname0:testsurname0\n"
               "testmail1@testmail.com:δοκιμαστικόόνομα:δοκιμαστικόεπίθετο\n"
               "testmail2@testmail.com:όνομα3:επίθετο3\n")
        reader = CSVReader(inp, 4)
        with pytest.raises(CSVCellError):
            next(reader)

    def test006_cells_more_that_max_fields(self):
        inp = ("testmail10testmail.com:testname0:testsurname0\n"
               "testmail1@testmail.com:δοκιμαστικόόνομα:δοκιμαστικόεπίθετο\n"
               "testmail2@testmail.com:όνομα3:επίθετο3\n")
        reader = CSVReader(inp, 1, 2)
        with pytest.raises(CSVCellError):
            next(reader)

    def test007_sample_picker_does_not_break_utf16be(self):
        # iso8859-7 doesn't have to be tested because every character is
        # encoded in 1 byte and cannot be broken
        # We test utf-16le and utf-16be because the .rpartition can make the
        # string end up with odd number of bytes(broken)
        # We also test the pick_sample with a broken utf-8 and see if it can
        # fix it
        inp = 'a\nb'
        inp = inp.encode('utf-16be')
        sample = pick_sample(inp)
        encoding = get_encoding(sample)
        assert encoding == 'utf-16be'

    def test008_sample_picker_does_not_break_utf16le(self):
        inp = 'test\u0a01input'
        inp = inp.encode('utf-16le')
        sample = pick_sample(inp)
        encoding = get_encoding(sample)
        assert encoding == 'utf-16le'

    def test009_sample_picker_fixes_utf_8(self):
        inp = ("The last char is multibyte in utf-8\n"
               "will be trancated ->\u0a01").encode('utf-8')
        broken_inp = inp[:-1]
        #broken_inp is broken and can't be decoded
        isBroken = False
        try:
            broken_inp.decode('utf-8')
        except UnicodeDecodeError:
            isBroken = True
        sample = pick_sample(broken_inp)
        encoding = get_encoding(sample)
        assert (encoding, isBroken) == ('utf-8', True)

    def test010_invalid_arguments_fields_are_zero(self):
        with pytest.raises(ValueError):
            CSVReader('', 0, 0)

    def test011_invalid_arguments_min_fields_more(self):
        with pytest.raises(ValueError):
            CSVReader('', 10, 1)

    def test012_check_delimiter_sniffing(self):
        delims = [',', ';', ':', ' ', '\t']
        inp = ("testmail10testmail.com{0}testname0{0}testsurname0\n"
               "testmail1@testmail.com{0}δοκιμαστικόόνομα{0}δοκεπίθετο\n"
               "testmail2@testmail.com{0}όνομα3{0}επίθετο3\n")
        delims_sniffed = []
        for delim in delims:
            delimed_input = inp.format(delim)
            dialect = get_dialect(delimed_input)
            delims_sniffed.append(dialect.delimiter)
        assert delims_sniffed == delims

    def test013_check_default_delimiter_is_comma(self):
        inp = 'stringwithnodelimiters\nanotherstring'
        dialect = get_dialect(inp)
        assert dialect.delimiter == ','


if __name__ == '__main__':
    main()
