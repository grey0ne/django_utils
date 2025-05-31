from django.db import models

def LocalizedStringField(verbose_name: str):
    return models.JSONField[dict[str, str]](
        null=True, blank=True, verbose_name=verbose_name
    )