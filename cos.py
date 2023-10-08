from __future__ import annotations

import abc
import dataclasses
import typing
import re

"""Carousel Object Structure"""


class ParseError(Exception): pass


class CosValue(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, string: bytes) -> tuple[typing.Self, bytes]:
        """Returns the parsed COS value and the remaining string."""
        raise ParseError

    def to_bytes(self) -> str:
        ...


@dataclasses.dataclass
class Null(CosValue):
    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[Null, bytes]:
        string = string.lstrip()

        if string.lower().startswith(b"null"):
            return cls(), string[4:]
        else:
            raise ParseError(f"Could not parse null from {string!r}.")


@dataclasses.dataclass
class Boolean(CosValue):
    value: bool

    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[Boolean, bytes]:
        string = string.lstrip().lower()

        if string.startswith(b"true"):
            return cls(True), string[4:]
        elif string.startswith(b"false"):
            return cls(False), string[5:]
        else:
            raise ParseError(f"Could not parse boolean from {string!r}.")


@dataclasses.dataclass
class String(CosValue):
    value: str

    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[String, bytes]:
        """
        Examples:
            (Testing)                   % ASCII
            (A\053B)                    % Same as (A+B)
            (Français)                  % PDFDocEncoded
            <FFFE0040>                  % Text with leading BOM
            (D:19990209153925-08'00')   % Date
            <1C2D3F>                    % Arbitrary binary data
        """
        string = string.strip()
        if string.startswith(b"("):
            # TODO: handle escape sequences, PDFDocEncoding
            try:
                end_i = string.index(b")")
            except ValueError:
                pass
            else:
                return cls(string[1:end_i].decode("utf-8")), string[end_i + 1:]

        elif string.startswith(b"<"):
            try:
                end_i = string.index(b">") + 1
            except ValueError as e:
                raise ParseError(f"Could not parse String from {string!r}.") from e
            else:
                string, remainder = string[:end_i], string[end_i:]
                string = string[1:-1].decode("utf-8").replace(" ", "")

                hex_nums_as_string = [elem for elem in zip(string[::2], string[1::2])]
                try:
                    return cls(''.join([chr(int(''.join(elem), 16)) for elem in hex_nums_as_string])), remainder
                except ValueError as e:
                    raise ParseError("String contains invalid hex literal.") from e

        else:
            raise ParseError(f"Could not parse String from {string!r}. "
                             f"Must be enclosed with either parentheses or angle brackets.")


@dataclasses.dataclass
class Number(CosValue):
    value: float | int

    _REGEX: typing.ClassVar[re.Pattern] = re.compile(rb"([+-]?(?:\d+(?:\.\d+)?)|(?:\.\d+))")

    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[Number, bytes]:
        """
        Examples:
            1
            -2
            +100
            612

            0.05
            .25
            -3.14159
            300.9001
        """

        match = cls._REGEX.match(string)
        if match is None:
            raise ParseError(f"Could not parse Number from {string!r}.")
        else:
            try:
                return cls(int(match.group())), string[match.end():]
            except ValueError:
                try:
                    return cls(float(match.group())), string[match.end():]
                except ValueError as e:
                    raise ParseError(f"Could not parse Number from {string!r}.") from e


_WHITESPACE = b"\x00\x09\x0A\x0C\x0D\x20"


@dataclasses.dataclass
class Name(CosValue):
    label: str

    _NONREGULAR_CHARACTERS: typing.ClassVar[re.Pattern] = re.compile("#[0-9A-Fa-f]{2}")

    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[Name, bytes]:
        """
        Examples:
            /Type
            /ThisIsName37
            /Lime#20Green
            /SSCN_SomeSecondClassName
        """
        string = string.lstrip()

        if not string.startswith(b"/"):
            raise ParseError(f"Invalid Name {string!r}. Must start with a slash/SOLIDUS (\"/\").")

        # remove slash
        string = string[1:]

        for i, char in enumerate(string):
            if not (0x21 < char < 0x7E) or bytes((char,)) in _WHITESPACE + b"/%[]<>{}()":
                # name ends here
                string, remainder = string[:i], string[i:]
                break
        else:
            # name ends at the end of the string
            string, remainder = string, b""

        string = string.decode("utf-8")

        try:
            string = re.sub(cls._NONREGULAR_CHARACTERS, lambda match: chr(int(match.group()[1:], 16)), string)
        except ValueError as e:
            raise ParseError("Name contains invalid hex literal.") from e

        return cls(string), remainder


@dataclasses.dataclass
class Array(CosValue):
    elements: list[CosValue]

    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[Array, bytes]:
        string = string.lstrip()

        if not string.startswith(b"["):
            raise ParseError("Array must be delimited by square brackets.")

        string = string[1:]

        elements: list[CosValue] = []

        while True:
            string = string.lstrip()
            try:
                element, string = parse_cos_value(string)
            except ParseError as e:
                if string.startswith(b"]"):
                    string = string[1:]
                    break
                else:
                    raise ParseError(f"Could not parse Array from {string!r}.") from e
            else:
                elements.append(element)

        return cls(elements), string


@dataclasses.dataclass
class Dictionary(CosValue):
    value: dict

    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[Dictionary, bytes]:
        string = string.lstrip()

        if not string.startswith(b"<<"):
            raise ParseError("Dictionary must be delimited by double angle brackets.")

        string = string[2:]

        value: dict = {}

        while True:
            string = string.lstrip()
            try:
                key, string = Name.from_bytes(string)
            except ParseError as e:
                if string.startswith(b">>"):
                    string = string[2:]
                    break
                else:
                    raise ParseError(f"Could not parse Dictionary from {string!r}.") from e
            else:
                string = string.lstrip()
                try:
                    value[key.label], string = parse_cos_value(string)
                except ParseError as e:
                    raise ParseError(f"Could not parse Dictionary from {string!r}.") from e

        return cls(value), string


@dataclasses.dataclass
class Stream(CosValue):
    stream_dict: Dictionary
    value: bytes

    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[Stream, bytes]:
        dictionary, string = Dictionary.from_bytes(string)

        string = string.lstrip()

        if not string.startswith(b"stream\n"):
            raise ParseError("Stream must be delimited by the stream keyword.")

        string = string[7:]

        try:
            out_bytes, remainder = string.split(b"\nendstream", 1)
        except ValueError as e:
            raise ParseError("Stream must be delimited by the endstream keyword.") from e

        return cls(dictionary, out_bytes), remainder


@dataclasses.dataclass
class Reference(CosValue):
    obj_num: int
    gen_num: int

    _REGEX: typing.ClassVar[re.Pattern] = re.compile(rb"(\d+)\s+(\d+)\s+R")

    @classmethod
    def from_bytes(cls, string: bytes) -> tuple[Reference, bytes]:
        string = string.lstrip()

        match = cls._REGEX.match(string)
        if match is None:
            raise ParseError(f"Invalid Reference {string!r}.")
        else:
            obj_num, gen_num = match.groups()
            return cls(int(obj_num), int(gen_num)), string[match.end():]


def parse_cos_value(string: bytes) -> tuple[CosValue, bytes]:
    types = Reference, Stream, Dictionary, String, Name, Array, Null, Boolean, Number

    for cos_type in types:
        try:
            return cos_type.from_bytes(string)
        except ParseError:
            pass

    raise ParseError
