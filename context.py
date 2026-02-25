import sys
import pyperclip
import contextlib
from io import StringIO

@contextlib.contextmanager
def clipboard_context():
    saved_stdout = sys.stdout
    output = StringIO()
    try:
        sys.stdout = output
        yield output
    finally:
        sys.stdout = saved_stdout
        pyperclip.copy(output.getvalue())

with open('IMG_5187.txt', 'r') as text_file:
    text_list = text_file.readlines()
# print(text_list)

with clipboard_context():
    all_strings = ' '.join(text_list)





