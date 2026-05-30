from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .buzz_client import BuzzApiError
from .reporting import clean_text, first_child, local_name, parse_xml


def extract_manifest_summary(
    manifest_xml: str, *, entityid: str, limit: int
) -> dict[str, Any]:
    """Normalize GetManifest into a bounded, depth-first content tree summary."""

    root = parse_xml(manifest_xml, "GetManifest payload")
    manifest = _find_first(root, "manifest")
    if manifest is None:
        raise BuzzApiError(
            "Response did not include a <manifest> element.",
            code="NOT_FOUND",
            details={"parser": "extract_manifest_summary"},
        )

    all_items: list[dict[str, Any]] = []
    for item in _direct_item_children(manifest):
        _walk_item(item, depth=0, path=[], items=all_items)

    items = all_items[:limit]
    return {
        "entityid": entityid,
        "schema_version": manifest.attrib.get("schema", ""),
        "version": manifest.attrib.get("version", ""),
        "resourceentityid": manifest.attrib.get("resourceentityid", ""),
        "count": len(items),
        "total_count": len(all_items),
        "limit": limit,
        "truncated": len(all_items) > len(items),
        "items": items,
    }


def _walk_item(
    item: ET.Element,
    *,
    depth: int,
    path: list[str],
    items: list[dict[str, Any]],
) -> None:
    itemid = item.attrib.get("id", "")
    data = first_child(item, "data")
    children = _direct_item_children(item)
    item_path = [*path, itemid] if itemid else path
    title = _data_text(data, "title") or itemid
    item_type = _data_text(data, "type") or ("Folder" if children else "")

    items.append(
        {
            "id": itemid,
            "title": title,
            "type": item_type,
            "parentid": _data_text(data, "parent"),
            "sequence": _data_text(data, "sequence"),
            "abbreviation": _data_text(data, "abbreviation"),
            "href": _data_text(data, "href"),
            "category": _data_text(data, "category"),
            "depth": depth,
            "path": item_path,
            "child_count": len(children),
            "partial": _bool_attr(item, "partial"),
            "resourceentityid": item.attrib.get("resourceentityid", ""),
        }
    )

    for child in children:
        _walk_item(child, depth=depth + 1, path=item_path, items=items)


def _find_first(root: ET.Element, name: str) -> ET.Element | None:
    wanted = name.lower()
    for element in root.iter():
        if local_name(element.tag) == wanted:
            return element
    return None


def _direct_item_children(element: ET.Element) -> list[ET.Element]:
    return [
        child
        for child in element
        if local_name(child.tag) in {"item", "_item"}
    ]


def _data_text(data: ET.Element | None, name: str) -> str:
    primary = first_child(data, name)
    if primary is None:
        primary = first_child(data, f"{name}_")
    return clean_text(primary)


def _bool_attr(element: ET.Element, name: str) -> bool:
    return (element.attrib.get(name) or "").lower() == "true"
