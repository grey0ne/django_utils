from enum import StrEnum
from typing import Literal

class Locale(StrEnum):
    RU = 'ru'
    EN = 'en'

LOCALE_LITERAL = Literal['ru', 'en']

DEFAULT_LOCALE = Locale.EN