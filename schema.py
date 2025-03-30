from enum import Enum

class Locale(str, Enum):
    RU = 'ru'
    EN = 'en'

DEFAULT_LOCALE = Locale.EN

LocalizedStringSchema = dict[Locale, str]