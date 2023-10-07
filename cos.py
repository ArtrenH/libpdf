from __future__ import annotations

"""Carousel Object Structure"""

import abc
import dataclasses
import typing
import re



class ParseError(Exception): pass




class CosValue(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_str(cls, string: str) -> typing.Self:
        ...
    
    def to_str(self) -> str:
        ...


@dataclasses.dataclass
class Null(CosValue):
    ...


@dataclasses.dataclass
class Boolean(CosValue):
    value: bool

    @classmethod
    def from_str(cls, string: str) -> Boolean:
        string = string.strip()

        try:
            return cls({"true": True, "false": False}[string])
        except KeyError as e:
            raise ParseError(f"Invalid boolean {string!r}.") from e


@dataclasses.dataclass
class String(CosValue):
    value: str

    @classmethod
    def from_str(cls, string: str) -> String:
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

        if string.startswith("(") and string.endswith(")"):
            return cls(string[1:-1])
        if string.startswith("<") and string.endswith(">"):
            string = string.replace(" ", "")
            string = string[1:-1]
            hex_nums_as_string = [elem for elem in zip(string[::2], string[1::2])]
            try:
                return cls(''.join([chr(int(''.join(elem), 16)) for elem in hex_nums_as_string]))
            except ValueError as e:
                raise ParseError("String contains invalid hex literal.") from e
        
        raise ParseError(f"Invalid String {string!r}. Must be enclosed with either parentheses or angle brackets.")



@dataclasses.dataclass
class Number(CosValue):
    value: float | int


@dataclasses.dataclass
class Name(CosValue):
    label: str

    _NONREGULAR_CHARACTERS: typing.ClassVar[re.Pattern] = re.compile("#\d\d")

    @classmethod
    def from_str(cls, string: str) -> Name:
        """
        Examples:
            /Type
            /ThisIsName37
            /Lime#20Green
            /SSCN_SomeSecondClassName
        """
        string = string.strip()

        if not string.startswith("/"):
            raise ParseError(f"Invalid Name {string!r}. Must start with a slash/SOLIDUS (\"/\").")
        
        # remove slash
        string = string[1:]

        try:
            string = re.sub(cls._NONREGULAR_CHARACTERS, lambda match: chr(int(match.group()[1:], 16)), string)
        except ValueError as e:
            raise ParseError("Name contains invalid hex literal.") from e

        return cls(string)


@dataclasses.dataclass
class Array(CosValue):
    elements: list[CosValue]

    @classmethod
    def from_str(cls, string: str) -> Array:
        string = string.strip()

        if not (string.startswith("[") and string.endswith("]")):
            raise ParseError("Array must be delimited by square brackets.")
    
        string = string[1:-1]

        elements: list[CosValue] = []

        while string:
            try:
                elements.append(parse_cos_value(substr))
            except ParseError:
                ...






@dataclasses.dataclass
class Dictionary(CosValue):
    value: dict

@dataclasses.dataclass
class NameTree(CosValue):
    value: dict


@dataclasses.dataclass
class Stream(CosValue):
    stream_dict: Dictionary
    value: bytes


def parse_cos_value(string: str) -> CosValue:
    types = Null, Boolean, String, Number, Name, Array, Dictionary, NameTree, Stream

    for cos_type in types:
        try:
            return cos_type.from_str(string)
        except ParseError:
            pass
    
    raise ParseError