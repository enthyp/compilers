class ConflictError(Exception):
    """Conflict in parsing table - non LL(1) grammar."""


class InputError(Exception):
    """Incorrect input string."""

