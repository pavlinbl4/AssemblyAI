from tkinter import filedialog
from pathlib import Path


def select_file():
    return filedialog.askopenfile(
        initialdir=f"{Path().home()}/Downloads",
        defaultextension=None, ).name


if __name__ == '__main__':
    select_file()
