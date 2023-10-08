import unittest
from cos import *


class TestNull(unittest.TestCase):
    def test_null(self):
        self.assertEqual(parse_cos_value(b"null"), (Null(), b""))
        self.assertEqual(parse_cos_value(b"null asd"), (Null(), b" asd"))


class TestBoolean(unittest.TestCase):
    def test_booleans(self):
        self.assertEqual(parse_cos_value(b"true"), (Boolean(True), b""))
        self.assertEqual(parse_cos_value(b"false"), (Boolean(False), b""))
        self.assertEqual(parse_cos_value(b"TRue"), (Boolean(True), b""))
        self.assertEqual(parse_cos_value(b"faLSE"), (Boolean(False), b""))
        self.assertEqual(parse_cos_value(b"true asd"), (Boolean(True), b" asd"))
        self.assertEqual(parse_cos_value(b"false asd"), (Boolean(False), b" asd"))


class TestString(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(parse_cos_value(b"(hello)"), (String.from_str("hello"), b""))
        self.assertEqual(parse_cos_value(b"(hello) asd"), (String.from_str("hello"), b" asd"))
        self.assertEqual(parse_cos_value(b"(hello world xyz)"), (String.from_str("hello world xyz"), b""))

    def test_escape(self):
        self.assertEqual(parse_cos_value(rb"(hello\053world)"), (String.from_str("hello+world"), b""))
        self.assertEqual(parse_cos_value(rb"(A\053B)"), (String.from_str("A+B"), b""))

    def test_pdf_doc_encoding(self):
        # TODO
        self.assertEqual(parse_cos_value(r"(Français)".encode("utf-8")), (String.from_str("Français"), b""))

    def test_binary(self):
        self.assertEqual(parse_cos_value(rb"<1C2D3F>"), (String.from_str(b"\x1c\x2d\x3f"), b""))
        self.assertEqual(parse_cos_value(rb"<3A5C7E>"), (String.from_str(b"\x3a\x5c\x7e"), b""))

    # def test_binary_bom(self):
    #     # bom = byte order mark
    #     self.assertEqual(parse_cos_value("<FFFE0040>"), (String.from_str(b"\xff\xfe\x00\x40"), ""))
    #     self.assertEqual(parse_cos_value("<FEFF0040>"), (String.from_str(b"\xfe\xff\x00\x40"), ""))

    def test_date(self):
        self.assertEqual(parse_cos_value(rb"(D:19990209153925-08'00')"), (String.from_str("D:19990209153925-08'00'"), b""))


class TestNumber(unittest.TestCase):
    def test_int(self):
        self.assertEqual(parse_cos_value(b"123"), (Number(123), b""))
        self.assertEqual(parse_cos_value(b"123 asd"), (Number(123), b" asd"))
        self.assertEqual(parse_cos_value(b"-123"), (Number(-123), b""))
        self.assertEqual(parse_cos_value(b"-123 asd"), (Number(-123), b" asd"))
        self.assertEqual(parse_cos_value(b"+123"), (Number(123), b""))
        self.assertEqual(parse_cos_value(b"+123 asd"), (Number(123), b" asd"))

    def test_real(self):
        self.assertEqual(parse_cos_value(b"0.05"), (Number(0.05), b""))
        self.assertEqual(parse_cos_value(b"0.05 asd"), (Number(0.05), b" asd"))
        self.assertEqual(parse_cos_value(b".25"), (Number(0.25), b""))
        self.assertEqual(parse_cos_value(b"-3.14159"), (Number(-3.14159), b""))
        self.assertEqual(parse_cos_value(b"+300.9001"), (Number(300.9001), b""))


class TestName(unittest.TestCase):
    def test_name(self):
        self.assertEqual(parse_cos_value(b"/Name"), (Name("Name"), b""))
        self.assertEqual(parse_cos_value(b"/Name asd"), (Name("Name"), b" asd"))
        self.assertEqual(parse_cos_value(b"/Name/Name"), (Name("Name"), b"/Name"))
        self.assertEqual(parse_cos_value(b"/Name#20"), (Name("Name "), b""))
        self.assertEqual(parse_cos_value(b"/Name#20asd"), (Name("Name asd"), b""))
        self.assertEqual(parse_cos_value(b"/Name#2F"), (Name("Name/"), b""))
        self.assertEqual(parse_cos_value(b"/Name#2Fasd"), (Name("Name/asd"), b""))


class TestArray(unittest.TestCase):
    def test_array(self):
        self.assertEqual(parse_cos_value(b"[]"), (Array([]), b""))
        self.assertEqual(parse_cos_value(b"[] asd"), (Array([]), b" asd"))
        self.assertEqual(parse_cos_value(b"[/Name]"), (Array([Name("Name")]), b""))
        self.assertEqual(parse_cos_value(b"[/Name] asd"), (Array([Name("Name")]), b" asd"))
        self.assertEqual(parse_cos_value(b"[/Name /Name]"), (Array([Name("Name"), Name("Name")]), b""))
        self.assertEqual(parse_cos_value(b"[/Name /Name] asd"), (Array([Name("Name"), Name("Name")]), b" asd"))

    def test_nested_array(self):
        self.assertEqual(parse_cos_value(b"[[]]"), (Array([Array([])]), b""))
        self.assertEqual(parse_cos_value(b"[[]] asd"), (Array([Array([])]), b" asd"))
        self.assertEqual(parse_cos_value(b"[[/Name]]"), (Array([Array([Name("Name")])]), b""))
        self.assertEqual(parse_cos_value(b"[[/Name]] asd"), (Array([Array([Name("Name")])]), b" asd"))
        self.assertEqual(parse_cos_value(b"[[/Name /Name]]"), (Array([Array([Name("Name"), Name("Name")])]), b""))


class TestReference(unittest.TestCase):
    def test_reference(self):
        self.assertEqual(parse_cos_value(b"1 2 R"), (Reference(1, 2), b""))
        self.assertEqual(parse_cos_value(b"1 0 R"), (Reference(1, 0), b""))
        self.assertEqual(parse_cos_value(b"1 2 R/Name"), (Reference(1, 2), b"/Name"))


class TestDictionary(unittest.TestCase):
    def test_dictionary(self):
        self.assertEqual(parse_cos_value(b"<<>>"), (Dictionary({}), b""))
        self.assertEqual(parse_cos_value(b"<<>> asd"), (Dictionary({}), b" asd"))
        self.assertEqual(parse_cos_value(b"<</Name/Name >>"), (Dictionary({"Name": Name("Name")}), b""))
        self.assertEqual(parse_cos_value(b"<</Name 0 0 R >>"), (Dictionary({"Name": Reference(0, 0)}), b""))
        self.assertEqual(parse_cos_value(b"<</Name[]>>"), (Dictionary({"Name": Array([])}), b""))
        self.assertEqual(parse_cos_value(b"<</Name<<>>>>"), (Dictionary({"Name": Dictionary({})}), b""))
        self.assertEqual(parse_cos_value(b"<</Length 3112/Subtype/XML/Type/Metadata>>"),
                         (Dictionary({"Length": Number(3112), "Subtype": Name("XML"), "Type": Name("Metadata")}), b""))
        self.assertEqual(
            parse_cos_value(b"<</Type /Page/Author (Leonard Rosenthol)/Resources << /Font [ /F1 /F2 ] >>>>"),
            (Dictionary({
                "Type": Name("Page"),
                "Author": String.from_str("Leonard Rosenthol"),
                "Resources": Dictionary({"Font": Array([Name("F1"), Name("F2")])})}
            ), b"")
        )


class TestStream(unittest.TestCase):
    def test_stream(self):
        a = b'<</Length 265/Filter/FlateDecode>>\nstream\nx\xc2\x9c]\xc2\x90\xc3\x8dn\xc2\x84 \x14\xc2\x85\xc3\xb7<\x05\xc3\x8b\xc2\x99\xc3\x85\x04\xc5\xbd:\xc3\x8e$\xc3\x86\xe2\x82\xac\xc2\xb11q\xc3\x91\xc2\x9f\xc3\x94\xc3\xb6\x01\x10\xc2\xae\xc2\x96d\x04\xc2\x82\xc5\xbe\xc3\xb0\xc3\xad\xc3\x8b\xc3\x8f\xc5\xbdM\xc2\xba\xc2\x80|7\xc3\xb7\x1c\xc5\xbe\xc3\xa7\xc2\x92\xc2\xb6\x7f\xc3\xaa\xc2\x95t\xc3\xa4\xc3\x8dj>\xc2\x80\xc3\x83\xc2\x93T\xc3\x82\xc3\x82\xc2\xaa7\xc3\x8b\x01\xc2\x8f0K\xc2\x85\xc2\xb2\x1c\x0b\xc3\x89\xc3\x9d\xc5\x93\xc2\x8a7_\xc2\x98A\xc3\x84{\xc2\x87}u\xc2\xb0\xc3\xb4j\xc3\x92u\xc2\x8d\xc3\x88\xc2\xbb\xc3\xaf\xc2\xad\xc3\x8e\xc3\xae\xc3\xb8\xc3\xb0(\xc3\xb4\x08GD^\xc2\xad +\xc3\x95\xc2\x8c\x0f\xc2\x9f\xc3\xad\xc3\xa0\xc3\xaba3\xc3\xa6\x06\x0b(\xc2\x87)j\x1a,`\xc3\xb2\xc3\xaf<3\xc3\xb3\xc3\x82\x16 \xc3\x91u\xc3\xaa\xc2\x85oK\xc2\xb7\xc2\x9f\xc5\x92\xc3\xa5O\xc3\xb0\xc2\xb1\x1b\xc3\x80y\xc2\xac\xc2\xb34\n\xc3\x97\x02V\xc3\x838X\xc5\xa0f@5\xc2\xa5\n\xc2\xae\xc2\xbb\xc2\xaeA\xc2\xa0\xc3\x84\xc2\xbf\xc3\x9e59\xc3\x86\xc2\x89\x7f1\xc3\xab\xc2\x95\xc2\x99WRZ\\\x1a\xc3\x8fy\xc3\xa4s\x19\xc3\xb8!q\x1b\xc5\xbeH\xc3\x9c\x05.#\xc3\xa74\xc3\xb09rY\x05\xc2\xae"Wy\xc3\xa0K\xc3\x92\x17\xc2\x81\xc2\xafI\xc2\x9f\xc3\x85Y\xc3\xae\xc2\xbf\xc2\x86\xc2\xa9\xc3\x82\xc3\x9a~\xc3\x92b\xc5\xb8Y\xc3\xab\xc2\x93\xc3\x86\xc3\x9d\xc3\x86\xc2\x88!\xc2\x9cT\xc3\xb0\xc2\xbb~\xc2\xa3Mp\xc3\x85\xc3\xb3\n\xc5\xa1Q\xc2\x80\x07\nendstream'

        self.assertIsInstance(parse_cos_value(a)[0], Stream)


if __name__ == '__main__':
    unittest.main()
