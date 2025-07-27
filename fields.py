from django.db import models
from dataorm.schema import LocalizedStringSchema

def LocalizedStringField(verbose_name: str) -> models.JSONField[LocalizedStringSchema]:
    return models.JSONField[LocalizedStringSchema](
        null=True, blank=True, verbose_name=verbose_name
    )