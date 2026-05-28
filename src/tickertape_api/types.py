"""Typed aliases for JSON payloads returned by Tickertape."""

from __future__ import annotations

from typing import Any, TypeAlias

JSON: TypeAlias = dict[str, Any] | list[Any] | str | int | float | bool | None
JSONObject: TypeAlias = dict[str, Any]
