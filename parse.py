from __future__ import annotations

import dataclasses
from pprint import pprint

import cos


class ParseError(Exception):
    pass


@dataclasses.dataclass
class Object:
    obj_num: int
    gen_num: int
    content: bytes
    parsed_content: cos.CosValue = dataclasses.field(init=False)

    def __post_init__(self):
        self.parsed_content = cos.parse_cos_value(self.content)[0]

    @classmethod
    def from_bytes(cls, byte_string: bytes) -> Object:
        lines = byte_string.split(b"\n")
        if not lines[0].endswith(b" obj"):
            raise ParseError("Invalid object: first line does not end with ' obj'")
        if not lines[-1] == b"endobj":
            raise ParseError("Invalid object: does not end with 'endobj'")
        obj_id, generation = lines[0].split(b" ")[:2]
        return cls(int(obj_id), int(generation), b"\n".join(lines[1:-1]))


@dataclasses.dataclass
class Header:
    content: bytes

    def __post_init__(self):
        if not self.content.startswith(b"%PDF-"):
            raise ParseError("Invalid header: does not start with '%PDF-'")
        self.version = self.extract_version()

    def extract_version(self) -> str:
        """Extracts the PDF version from the header."""
        return self.content.decode("utf-8").split("\n")[0].split("-")[-1]


@dataclasses.dataclass
class Body:
    content: bytes
    objects: dict[tuple[int, int], Object] = dataclasses.field(init=False)

    def __post_init__(self):
        self.extract_objects()
        self.resolve_references()

    def extract_objects(self) -> None:
        """Extracts all objects from the body."""
        self.objects = {}
        lines = self.content.split(b"\n")
        object_starts = [i for i, line in enumerate(lines) if line.endswith(b" obj")]
        object_ends = [i for i, line in enumerate(lines) if line == b"endobj"]
        if len(object_starts) != len(object_ends):
            raise ParseError("Invalid body: number of object starts and ends do not match.")
        for start, end in zip(object_starts, object_ends):
            cur_object = Object.from_bytes(b"\n".join(lines[start:end + 1]))
            self.objects[cur_object.obj_num, cur_object.gen_num] = cur_object

    def resolve_references(self):
        lookup = {(obj.obj_num, obj.gen_num): obj.parsed_content for obj in self.objects.values()}

        for obj in self.objects.values():
            if isinstance(obj.parsed_content, cos.CosValue):
                obj.parsed_content.replace_references(lookup)
            else:
                raise ParseError(f"Invalid object: {obj.parsed_content!r} is not a CosValue.")


@dataclasses.dataclass
class CrossReferenceTable:
    content: bytes


@dataclasses.dataclass
class Trailer:
    content: bytes
    parsed_content: cos.Dictionary = dataclasses.field(init=False)

    def __post_init__(self):
        if not self.content.startswith(b"trailer\n"):
            raise ParseError("Invalid trailer: does not start with b'trailer\\n'.")

        _, trailer_data_start = self.content.split(b"\n", 1)

        self.parsed_content = cos.parse_cos_value(trailer_data_start)[0]


@dataclasses.dataclass
class PdfSplitter:
    string: bytes
    lines: list[bytes] = dataclasses.field(init=False)

    def __post_init__(self):
        self.lines = self.string.split(b"\n")

    def find_header_start(self) -> int:
        for i, line in enumerate(self.lines):
            if line.startswith(b"%PDF-"):
                return i
        raise ParseError("Could not find start of header.")

    def find_first_object(self) -> int:
        for i, line in enumerate(self.lines):
            if line.endswith(b" obj"):
                return i
        raise ParseError("Could not find start of body.")

    def find_cross_reference_table(self) -> int:
        for i, line in enumerate(self.lines):
            if line == b"xref":
                return i
        raise ParseError("Could not find start of cross reference table.")

    def find_trailer(self) -> int:
        for i, line in enumerate(self.lines):
            if line == b"trailer":
                return i
        raise ParseError("Could not find start of trailer.")


@dataclasses.dataclass
class PdfFile:
    header: Header
    body: Body
    cross_reference_table: CrossReferenceTable
    trailer: Trailer
    content: bytes = dataclasses.field(init=False)

    def __post_init__(self):
        self.content = b"\n".join(
            [
                self.header.content,
                self.body.content,
                self.cross_reference_table.content,
                self.trailer.content,
            ]
        )

    @classmethod
    def from_file(cls, filepath: str) -> PdfFile:
        with open(filepath, "rb") as f:
            return cls.from_bytes(f.read())

    @classmethod
    def from_bytes(cls, byte_string: bytes) -> PdfFile:
        lines = byte_string.split(b"\n")
        pdf_splitter = PdfSplitter(byte_string)
        header_start = pdf_splitter.find_header_start()
        body_start = pdf_splitter.find_first_object()
        cross_reference_table_start = pdf_splitter.find_cross_reference_table()
        trailer_start = pdf_splitter.find_trailer()
        return cls(
            Header(b"\n".join(lines[header_start:body_start])),
            Body(b"\n".join(lines[body_start:cross_reference_table_start])),
            CrossReferenceTable(b"\n".join(lines[cross_reference_table_start:trailer_start])),
            Trailer(b"\n".join(lines[trailer_start:])),
        )


@dataclasses.dataclass
class MediaBox:
    lower_left_x: float
    lower_left_y: float
    upper_right_x: float
    upper_right_y: float

    @classmethod
    def from_cos_array(cls, cos_value: cos.Array) -> MediaBox:
        return cls(
            cos_value.elements[0].value,
            cos_value.elements[1].value,
            cos_value.elements[2].value,
            cos_value.elements[3].value,
        )


if __name__ == "__main__":
    # p = PdfFile.from_file("sample_pdf/hello_world_example_oreilly.pdf")
    p2 = PdfFile.from_file("sample_pdf/hello_world_libreoffice.pdf")

    root_reference: cos.Reference = p2.trailer.parsed_content["Root"]
    root_object = p2.body.objects[root_reference.obj_num, root_reference.gen_num].parsed_content
    for page in root_object["Pages"]["Kids"].elements:
        print("Type:", page["Type"])
        print("MediaBox:", MediaBox.from_cos_array(page["MediaBox"]))
        print("Content:")
        print(page["Contents"].decode().decode("utf-8"))
        with open("font.ttf", "wb") as f:
            f.write(page["Resources"]["Font"]["F1"]["FontDescriptor"]["FontFile2"].decode())
