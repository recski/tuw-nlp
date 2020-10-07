import re


CHAR_PATT = re.compile(r'start_char=([0-9]*)\|end_char=([0-9]*)')

CHAR_REPLACEMENTS = {
    "ö": 'oe',
    "Ö": 'Oe',
    "ü": 'ue',
    "Ü": 'Ue',
    "ä": 'ae',
    "Ä": 'Ae',
    "ß": "ss",
}

PUNCT_REPLACEMENTS = {
    "+": "PLUS",
    "/": "SLASH",
    "_": "UNDERSCORE",
    "-": "HYPHEN",
    "(": "LRB",
    ")": "RRB",
    ".": "PERIOD",
    ",": "COMMA",
    ":": "COLON",
    ";": "SEMICOLON",
    "%": "PERCENTAGE",
    "°": "XDEGREE",
    "§": "PARAGRAPH",
    "§§": "PARAGRAPHS",
    "„": "QUOTE",
    "“": "QUOTE",
    "'": "QUOTE",
    '"': "QUOTE",
    '²': "SQUARE"
    }

MISC_REPLACEMENTS = {
    "m²": "m2",
    "m³": "m3"}
