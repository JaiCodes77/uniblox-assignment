from collections.abc import Callable
from contextlib import contextmanager
from typing import Iterator

from fastapi import HTTPException

from app.services.errors import NotFoundError


@contextmanager
def service_errors() -> Iterator[None]:
    """Translate service-layer exceptions to HTTPException.

    - ``NotFoundError`` → 404
    - any other ``ValueError`` → 400
    """
    try:
        yield
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# Convenience for places that don't want the `with` form.
def map_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    raise exc


__all__: list[Callable | str] = ["service_errors", "map_service_error"]
