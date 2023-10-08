from cos import *

print(String.from_bytes(b"(A\\053B)"))
print(Name.from_bytes(b"/Lime#20GreenName#2F/Name"))
print(parse_cos_value(b"[]"))
print(parse_cos_value(b"[[/Name 02 null True (AsdAsd) <3A5C7E>]]"))
print(parse_cos_value(b"<< /Name/Name >>"))
print(parse_cos_value(b"<</Type /Page/Author (Leonard Rosenthol)/Resources << /Font [ /F1 /F2 ] >>>>"))
