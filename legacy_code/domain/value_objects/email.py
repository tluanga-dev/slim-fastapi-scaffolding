import re
from typing import Any


class Email:
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    def __init__(self, value: str):
        if not self.EMAIL_REGEX.match(value):
            raise ValueError(f"Invalid email format: {value}")
        self._value = value.lower()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Email('{self._value}')"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Email):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)