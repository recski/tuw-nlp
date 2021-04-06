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
    "ō": "oe",  # encountered in plandok (OCR err?)
}

PUNCT_REPLACEMENTS = {
    "+": "PLUS",
    "/": "SLASH",
    "_": "UNDERSCORE",
    "-": "HYPHEN",
    "–": "ENDASH",
    "(": "LRB",
    ")": "RRB",
    "<": "LT",
    ">": "GT",
    ".": "PERIOD",
    ",": "COMMA",
    ":": "COLON",
    "!": "EXCL",
    "?": "QUE",
    ";": "SEMICOLON",
    "%": "PERCENTAGE",
    "°": "XDEGREE",
    "§": "PARAGRAPH",
    "§§": "PARAGRAPHS",
    "„": "QUOTE",
    "“": "QUOTE",
    '”': "QUOTE",
    "'": "QUOTE",
    '"': "QUOTE",
    '²': "SQUARE",
    '³': "CUBE",
    "\uf0b7": "INVALID",
    "@": "ATSYMBOL",
    "&": "AMPERSAND",
    "#": "HASHTAG"
    }

MISC_REPLACEMENTS = {
    "m²": "m2",
    "m³": "m3"}
