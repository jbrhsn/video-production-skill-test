"""Resolve composable style and brand policy into one renderable production grammar."""
from __future__ import annotations

import copy
import hashlib
import json

from contracts import text


def _merge(base, addition, provenance, origin, prefix=""):
    for key, value in addition.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            target = base.setdefault(key, {})
            if not isinstance(target, dict):
                raise ValueError(f"style conflict at {path}")
            _merge(target, value, provenance, origin, path)
        else:
            base[key] = copy.deepcopy(value)
            provenance[path] = origin


def resolve_style(catalog, request, brand=None, overrides=None):
    if not isinstance(catalog, dict) or catalog.get("version") != 2 or not isinstance(catalog.get("profiles"), dict):
        raise ValueError("style catalog requires version 2 and profiles")
    if not isinstance(request, dict) or set(request) != {"profile"}:
        raise ValueError("style request requires profile")
    profile_id = text(request.get("profile"), "style profile")
    profile = catalog["profiles"].get(profile_id)
    if not isinstance(profile, dict):
        raise ValueError(f"unknown style profile: {profile_id}")
    resolved, provenance = {}, {}
    _merge(resolved, profile, provenance, f"profile:{profile_id}")
    if brand is not None:
        if not isinstance(brand, dict) or set(brand) - {"id", "tokens", "prohibited", "exceptions"}:
            raise ValueError("brand permits id, tokens, prohibited, and exceptions")
        tokens = brand.get("tokens", {})
        if not isinstance(tokens, dict):
            raise ValueError("brand.tokens must be an object")
        _merge(resolved, tokens, provenance, "brand")
        prohibited = brand.get("prohibited", [])
        if not isinstance(prohibited, list) or any(not isinstance(value, str) or not value for value in prohibited):
            raise ValueError("brand.prohibited must be a list of nonempty strings")
        resolved["prohibited"] = prohibited
        provenance["prohibited"] = "brand"
        exceptions = brand.get("exceptions", [])
        if not isinstance(exceptions, list) or any(not isinstance(value, dict) or set(value) != {"field", "reason", "approvedBy"} or any(not isinstance(value[key], str) or not value[key] for key in value) for value in exceptions):
            raise ValueError("brand.exceptions must contain field, reason, and approvedBy")
        resolved["brandExceptions"] = exceptions
        provenance["brandExceptions"] = "brand"
    if overrides is not None:
        if not isinstance(overrides, dict):
            raise ValueError("style overrides must be an object")
        _merge(resolved, overrides, provenance, "project")
    payload = {"schema": "resolved-style", "version": 2, "profile": profile_id,
               "values": resolved, "provenance": provenance}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return {**payload, "digest": hashlib.sha256(encoded).hexdigest()}
