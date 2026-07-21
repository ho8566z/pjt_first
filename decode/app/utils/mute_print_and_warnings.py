from contextlib import redirect_stderr, redirect_stdout
import os
from functools import wraps


def mute_print_and_warnings(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with open(os.devnull, "w") as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                return func(*args, **kwargs)

    return wrapper
