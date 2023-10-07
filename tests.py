import unittest
from cos import *


class TestNull(unittest.TestCase):
    def test_null(self):
        self.assertEqual(parse_cos_value("null"), (Null(), ""))
        self.assertEqual(parse_cos_value("null asd"), (Null(), " asd"))


class TestBoolean(unittest.TestCase):
    def test_booleans(self):
        self.assertEqual(parse_cos_value("true"), (Boolean(True), ""))
        self.assertEqual(parse_cos_value("false"), (Boolean(False), ""))
        self.assertEqual(parse_cos_value("TRue"), (Boolean(True), ""))
        self.assertEqual(parse_cos_value("faLSE"), (Boolean(False), ""))
        self.assertEqual(parse_cos_value("true asd"), (Boolean(True), " asd"))
        self.assertEqual(parse_cos_value("false asd"), (Boolean(False), " asd"))


class TestString(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(parse_cos_value("(hello)"), (String("hello"), ""))
        self.assertEqual(parse_cos_value("(hello) asd"), (String("hello"), " asd"))
        self.assertEqual(parse_cos_value("(hello world xyz)"), (String("hello world xyz"), ""))

    def test_escape(self):
        self.assertEqual(parse_cos_value(r"(hello\053world)"), (String("hello+world"), ""))
        self.assertEqual(parse_cos_value(r"(A\B)"), (String("A+B"), ""))

    def test_pdf_doc_encoding(self):
        # TODO
        self.assertEqual(parse_cos_value(r"(Français)"), (String("Français"), ""))

    def test_binary(self):
        self.assertEqual(parse_cos_value(r"<1C2D3F>"), (String("\x1c\x2d\x3f"), ""))
        self.assertEqual(parse_cos_value(r"<3A5C7E>"), (String("\x3a\x5c\x7e"), ""))

    # def test_binary_bom(self):
    #     # bom = byte order mark
    #     self.assertEqual(parse_cos_value("<FFFE0040>"), (String(b"\xff\xfe\x00\x40"), ""))
    #     self.assertEqual(parse_cos_value("<FEFF0040>"), (String(b"\xfe\xff\x00\x40"), ""))

    def test_date(self):
        self.assertEqual(parse_cos_value(r"(D:19990209153925-08'00')"), (String("D:19990209153925-08'00'"), ""))


class TestNumber(unittest.TestCase):
    def test_int(self):
        self.assertEqual(parse_cos_value("123"), (Number(123), ""))
        self.assertEqual(parse_cos_value("123 asd"), (Number(123), " asd"))
        self.assertEqual(parse_cos_value("-123"), (Number(-123), ""))
        self.assertEqual(parse_cos_value("-123 asd"), (Number(-123), " asd"))
        self.assertEqual(parse_cos_value("+123"), (Number(123), ""))
        self.assertEqual(parse_cos_value("+123 asd"), (Number(123), " asd"))

    def test_real(self):
        self.assertEqual(parse_cos_value("0.05"), (Number(0.05), ""))
        self.assertEqual(parse_cos_value("0.05 asd"), (Number(0.05), " asd"))
        self.assertEqual(parse_cos_value(".25"), (Number(0.25), ""))
        self.assertEqual(parse_cos_value("-3.14159"), (Number(-3.14159), ""))
        self.assertEqual(parse_cos_value("+300.9001"), (Number(300.9001), ""))


class TestName(unittest.TestCase):
    def test_name(self):
        self.assertEqual(parse_cos_value("/Name"), (Name("Name"), ""))
        self.assertEqual(parse_cos_value("/Name asd"), (Name("Name"), " asd"))
        self.assertEqual(parse_cos_value("/Name/Name"), (Name("Name"), "/Name"))
        self.assertEqual(parse_cos_value("/Name#20"), (Name("Name "), ""))
        self.assertEqual(parse_cos_value("/Name#20asd"), (Name("Name asd"), ""))
        self.assertEqual(parse_cos_value("/Name#2F"), (Name("Name/"), ""))
        self.assertEqual(parse_cos_value("/Name#2Fasd"), (Name("Name/asd"), ""))


class TestArray(unittest.TestCase):
    def test_array(self):
        self.assertEqual(parse_cos_value("[]"), (Array([]), ""))
        self.assertEqual(parse_cos_value("[] asd"), (Array([]), " asd"))
        self.assertEqual(parse_cos_value("[/Name]"), (Array([Name("Name")]), ""))
        self.assertEqual(parse_cos_value("[/Name] asd"), (Array([Name("Name")]), " asd"))
        self.assertEqual(parse_cos_value("[/Name /Name]"), (Array([Name("Name"), Name("Name")]), ""))
        self.assertEqual(parse_cos_value("[/Name /Name] asd"), (Array([Name("Name"), Name("Name")]), " asd"))

    def test_nested_array(self):
        self.assertEqual(parse_cos_value("[[]]"), (Array([Array([])]), ""))
        self.assertEqual(parse_cos_value("[[]] asd"), (Array([Array([])]), " asd"))
        self.assertEqual(parse_cos_value("[[/Name]]"), (Array([Array([Name("Name")])]), ""))
        self.assertEqual(parse_cos_value("[[/Name]] asd"), (Array([Array([Name("Name")])]), " asd"))
        self.assertEqual(parse_cos_value("[[/Name /Name]]"), (Array([Array([Name("Name"), Name("Name")])]), ""))


if __name__ == '__main__':
    unittest.main()
