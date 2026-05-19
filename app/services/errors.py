class NotFoundError(ValueError):
    """Raised by services when a referenced resource doesn't exist.

    Subclasses ``ValueError`` so existing call sites that catch ValueError
    continue to work; routes catch ``NotFoundError`` first to map to 404
    and fall back to ValueError → 400.
    """
