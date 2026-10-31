# django_utils

Shared Django helpers for personal projects (django-ninja + dataclass-based ORM querying). Used as a git submodule at `<project>/backend/django_utils` in several projects — keep it project-agnostic.

Host projects import it as a top-level package (`from django_utils.api import ...`) and their settings do `from django_utils.base_settings import *`.

## Modules

- `api.py` — endpoint decorators wrapping a ninja `Router`: `single_item`, `id_paginated`, `unpaginated_list`, `action` (POST), plus `get_single_item_or_404`. Default auth is `django_auth` from `auth.py`; pass `auth=None` for public endpoints.
- `queries.py` — the "dataorm" core: builds `.values()` queries from dataclass field definitions and returns typed dataclasses (`typed_data_list`, `typed_data_dict`, `dict_from_dataclass`, nested/related field handling, file/base64 fields).
- `queries_helpers.py` — type introspection helpers used by `queries.py`.
- `schema.py` — shared types (`DataclassProtocol`, `Error`, `EmptyResponse`, `Locale`, `LOCALES`, login/translation payloads).
- `pagination.py` — `IDPagination`, `DateIDPagination` (cursor-style).
- `auth.py`, `jwt.py`, `middleware.py` — JWT-cookie session engine (`SESSION_ENGINE = "django_utils.jwt"`), async auth classes, domain routing middleware.
- `api_enpoints.py` — shared auth/translation endpoints.
- `base_settings.py` — base Django settings driven by env vars (`settings_helpers.config_get_str`): S3 storage, static/media domains, Sentry, JWT, cookies.
- `models.py` — `BaseUser` (AbstractUser).
- `chatgpt.py` — OpenAI async client helpers (text + image generation).
- `auth_backends.py`, `i18n.py`, `fields.py`, `helpers.py`, `constants.py` — misc helpers.

## Conventions

- Response/request schemas are frozen `@dataclass`es (`slots=True, kw_only=True`), not ninja `Schema` classes.
- Code is async-first (async views and ORM calls).
- Strictly typed for mypy with `django-stubs`; some `# type: ignore` are needed where ninja lacks typing.
- No tests live here; verify changes against a host project (`./deploy/dc django check`, mypy).
