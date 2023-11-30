import re
import os
from textwrap import dedent

def _dedent_and_trim(text):
    return re.sub(r'^\s*\n', '', dedent(text).rstrip())

class Doc:
    def __init__(self):
        self.text = ""

    def append(self, text):
        self.text += str(text)
        return self

    def append_with_newline(self, text, num_newlines=1):
        self.text = self.text.rstrip() + (os.linesep * num_newlines if self.text.strip() else "") + _dedent_and_trim(text)
        return self