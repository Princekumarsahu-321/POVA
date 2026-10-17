"""Open only preconfigured websites."""

import webbrowser

from config.commands import WEBSITES
from actions import ActionError


def open_website(key: str) -> str:
    website = WEBSITES.get(key)
    if website is None:
        raise ActionError("That website is not on the allowlist.")
    name, url, _aliases = website
    if not webbrowser.open_new_tab(url):
        raise ActionError(f"Could not open {name} in the browser.")
    return f"Opening {name}."
