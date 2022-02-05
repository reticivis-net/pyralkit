import typing
from dataclasses import dataclass


class PKException(Exception):
    """
    base class for PyralKit exceptions
    """


class PKFailed(PKException):
    """Generic fail"""


class PKNotAuthorized(PKException):
    """Raised when user attempts to do something that requires authorization, but they aren't authorized."""

    def __init__(self):
        super().__init__("This function requires authorization.")


@dataclass
class PKErrorObject:
    """https://pluralkit.me/api/errors/#error-object"""

    message: str
    max_length: typing.Optional[int] = None
    actual_length: typing.Optional[int] = None


@dataclass
class PKErrorResponse(PKException):
    """https://pluralkit.me/api/errors/#error-response-model"""

    code: int
    message: str
    http_code: int
    errors: typing.Optional[typing.List[PKErrorObject]] = None
    retry_after: typing.Optional[int] = None

    def __post_init__(self):
        super().__init__(f"Error {self.code}: {self.message}")


@dataclass
class PKBadRequest(PKErrorResponse):
    """HTTP 400"""

    http_code: int = 400
    pass


@dataclass
class PKUnauthorized(PKErrorResponse):
    """HTTP 401"""

    http_code: int = 401
    pass


@dataclass
class PKForbidden(PKErrorResponse):
    """HTTP 403"""

    http_code: int = 403
    pass


@dataclass
class PKNotFound(PKErrorResponse):
    """HTTP 404"""

    http_code: int = 404
    pass


http_errors = {
    400: PKBadRequest,
    401: PKUnauthorized,
    403: PKForbidden,
    404: PKNotFound,
}
