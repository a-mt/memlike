import re
from unidecode import unidecode


def slugify(text):
    if not text:
        return ""

    text = unidecode(text).lower()
    text = re.sub(r"[^a-z0-9-]", "-", text)
    text = re.sub("-+", "-", text)
    return text.strip("-")
