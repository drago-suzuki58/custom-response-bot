class FunctionDirectiveError(Exception):
    def __init__(self, public_message: str, *, log_message: str | None = None):
        super().__init__(public_message)
        self.public_message = public_message
        self.log_message = log_message
