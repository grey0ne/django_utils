from django.db import models
from django_utils.schema import LocalizedStringSchema, Locale, LOCALES

def LocalizedStringField(verbose_name: str) -> models.JSONField[LocalizedStringSchema]:
    return models.JSONField[LocalizedStringSchema](
        null=True, blank=True, verbose_name=verbose_name
    )

def LocaleField(verbose_name: str, default: str = Locale.EN) -> models.CharField[str, str]:
    return models.CharField(
        null=True, blank=True, verbose_name=verbose_name, max_length=2, choices=LOCALES, default=default
    )