import re


# based on https://stackoverflow.com/a/49986645
EMOJI_PATT = re.compile(
    pattern="["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+", flags=re.UNICODE)

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
    "é": "e1",
    "è": "e1",
    "ï": "i2"
}

PUNCT_REPLACEMENTS = {
    "+": "PLUS",
    "/": "SLASH",
    "\\": "BACKSLASH",
    "_": "UNDERSCORE",
    "-": "HYPHEN",
    "–": "ENDASH",
    "—": "EMDASH",
    "(": "LRB",
    ")": "RRB",
    "{": "LCB",
    "}": "RCB",
    "[": "LSB",
    "]": "RSB",
    "<": "LT",
    ">": "GT",
    "^": "CARET",
    ".": "PERIOD",
    "·": "CDOT",
    "…": "LDOTS",
    ",": "COMMA",
    ":": "COLON",
    "!": "EXCL",
    "?": "QUE",
    ";": "SEMICOLON",
    "%": "PERCENTAGE",
    "$": "DOLLAR",
    "°": "XDEGREE",
    "§": "PARAGRAPH",
    "§§": "PARAGRAPHS",
    "„": "QUOTE",
    "“": "QUOTE",
    '”': "QUOTE",
    "'": "QUOTE",
    '"': "QUOTE",
    '‘': "QUOTE",
    '²': "SQUARE",
    '³': "CUBE",
    "@": "ATSYMBOL",
    "&": "AMPERSAND",
    "#": "HASHTAG",
    "~": "TILDE",
    "*": "ASTERISK",
    "∞": "INFINITY",
    "=": "EQUALS"
    }

MISC_REPLACEMENTS = {
    "m²": "m2",
    "m³": "m3",
    "\uf0b7": "INVALID",
    "\uf818": "INVALID",
    "\uf0e0": "INVALID",
    "\u200B": "INVALID"
    }
