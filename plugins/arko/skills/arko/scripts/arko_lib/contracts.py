"""Conservative compatibility guard; not a complete OpenAPI semantic diff."""

import re
from urllib.parse import unquote

HTTP_METHODS = frozenset({"get", "put", "post", "delete", "options", "head", "patch", "trace"})
METADATA_KEYS = frozenset({"description", "summary", "title", "examples", "example"})


def openapi_routes(schema: dict) -> set[tuple[str, str]]:
    return {
        (method.upper(), path)
        for path, item in schema.get("paths", {}).items()
        for method in item
        if method in HTTP_METHODS
    }


def declared_public_routes(features: dict) -> list[tuple[str, str, str]]:
    expected = []
    for feature, entry in features.items():
        routes = entry.get("public_routes", [])
        if not isinstance(routes, list):
            raise ValueError(f"{feature}: public_routes must be a list of 'METHOD /path' strings")
        for route in routes:
            match = re.fullmatch(r"([A-Z]+) (/[^\s?#]*)", route) if isinstance(route, str) else None
            if match is None or match[1].lower() not in HTTP_METHODS:
                raise ValueError(f"{feature}: invalid public route {route!r}; expected 'METHOD /path'")
            expected.append((feature, match[1], match[2]))
    return expected


def json_equal(old: object, new: object) -> bool:
    if isinstance(old, bool) != isinstance(new, bool):
        return False
    if isinstance(old, list) and isinstance(new, list):
        return len(old) == len(new) and all(json_equal(a, b) for a, b in zip(old, new))
    if isinstance(old, dict) and isinstance(new, dict):
        return old.keys() == new.keys() and all(json_equal(value, new[key]) for key, value in old.items())
    return old == new


def _response_references(schema: dict) -> set[tuple[str, ...]]:
    references: set[tuple[str, ...]] = set()

    def visit(value: object) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/"):
                parts = tuple(part.replace("~1", "/").replace("~0", "~")
                              for part in unquote(ref[2:]).split("/"))
                if parts not in references:
                    references.add(parts)
                    target = schema
                    for part in parts:
                        target = target.get(part) if isinstance(target, dict) else None
                    visit(target)
            for item in value.values():
                visit(item)

    for method, path in openapi_routes(schema):
        operation = schema["paths"][path][method.lower()]
        visit(operation.get("responses", {}))
    return references


def compatible(old: object, new: object, path: str = "$") -> list[str]:
    references = _response_references(old) if isinstance(old, dict) else set()
    return _compatible(old, new, path, (), references)


def _added_keys(
    keys: set[str], path: str, location: tuple[str, ...], named_map: bool, closed_properties: bool
) -> list[str]:
    if closed_properties:
        return [f"{path}.{key}: new property in a closed schema requires review" for key in sorted(keys)]
    if path in {"$.paths", "$.components.schemas"} or path.endswith(".properties"):
        return []
    if location[:1] == ("paths",) and len(location) == 2:
        keys -= HTTP_METHODS
    if not named_map:
        keys -= METADATA_KEYS
    return [f"{path}.{key}: new constraint/structure requires review" for key in sorted(keys)]


def _compatible(
    old: object,
    new: object,
    path: str,
    location: tuple[str, ...],
    response_refs: set[tuple[str, ...]],
    *,
    closed_properties: bool = False,
) -> list[str]:
    errors = []
    if isinstance(old, dict) and isinstance(new, dict):
        named_map = path.endswith(
            (".properties", ".schemas", ".paths", ".responses", ".content", ".securitySchemes")
        )
        closed_response = old.get("additionalProperties") is False and (
            (location[:1] == ("paths",) and location[3:4] == ("responses",))
            or any(location[:len(ref)] == ref for ref in response_refs)
        )
        for key, value in old.items():
            if not named_map and key in METADATA_KEYS:
                continue
            if key not in new:
                errors.append(f"{path}.{key}: removed")
            else:
                errors.extend(_compatible(
                    value, new[key], f"{path}.{key}", (*location, key), response_refs,
                    closed_properties=key == "properties" and closed_response,
                ))
        errors.extend(_added_keys(new.keys() - old.keys(), path, location, named_map, closed_properties))
    elif not json_equal(old, new):
        errors.append(f"{path}: changed; potentially incompatible")
    return errors
