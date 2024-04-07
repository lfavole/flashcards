class Progress:
    """A utility that print a progress message and its confirmation."""

    def __init__(self, message):
        self.message = message

    def __enter__(self):
        print(f"{self.message}... ", end="", flush=True)
        return self

    def __exit__(self, exc, value, tb):
        if exc:
            print("ERROR: ", end="", flush=True)
        else:
            print("OK", flush=True)
