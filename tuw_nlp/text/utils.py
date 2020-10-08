def normalize_whitespace(text):
    nt = text.strip()
    if nt == "":
        return ""
    return " ".join([s for s in text.split() if s])
