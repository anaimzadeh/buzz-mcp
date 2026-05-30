from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .buzz_client import BuzzApiError
from .reporting import clean_text, first_child, local_name, parse_xml


def extract_item_summary(
    item_xml: str, *, entityid: str, requested_itemid: str
) -> dict[str, Any]:
    """Normalize GetItem into a conservative item metadata summary."""

    root = parse_xml(item_xml, "GetItem/GetItemList payload")
    item = _find_item_element(root)
    if item is None:
        raise BuzzApiError(
            "Response did not include an <item> element.",
            code="NOT_FOUND",
            details={"parser": "extract_item_summary"},
        )

    data = first_child(item, "data")
    if data is None:
        raise BuzzApiError(
            "Item response missing <data> block.",
            code="NOT_FOUND",
            details={"parser": "extract_item_summary"},
        )

    itemid = item.attrib.get("id") or item.attrib.get("itemid") or requested_itemid
    title = _data_text(data, "title") or itemid

    return {
        "entityid": entityid,
        "id": itemid,
        "title": title,
        "type": _data_text(data, "type"),
        "parentid": _data_text(data, "parent"),
        "sequence": _data_text(data, "sequence"),
        "abbreviation": _data_text(data, "abbreviation"),
        "href": _data_text(data, "href"),
        "folder": _data_text(data, "folder"),
        "category": _data_text(data, "category"),
        "period": _data_text(data, "period"),
        "resourceentityid": item.attrib.get("resourceentityid", ""),
        "creation_date": item.attrib.get("creationdate", ""),
        "modified_date": item.attrib.get("modifieddate", ""),
        "version": item.attrib.get("version", ""),
        "origin_depth": item.attrib.get("origindepth", ""),
        "derivative_depth": item.attrib.get("derivativedepth", ""),
        "due_date": _data_text(data, "duedate"),
        "available_date": _data_text(data, "availabledate"),
        "gradable": _data_bool(data, "gradable"),
        "allow_late_submission": _data_bool(data, "allowlatesubmission"),
        "perfect_score": _data_text(data, "perfectscore"),
        "weight": _data_text(data, "weight"),
        "accepts_file_upload": _accepts_file_upload(data),
        "allowed_filetypes": _dropbox_filetypes(data),
        "dropbox_multiple": _dropbox_multiple(data),
    }


def _find_item_element(root: ET.Element) -> ET.Element | None:
    for element in root.iter():
        if local_name(element.tag) == "item":
            return element
    return None


def _data_text(data: ET.Element, name: str) -> str:
    primary = first_child(data, name)
    if primary is None:
        primary = first_child(data, f"{name}_")
    return clean_text(primary)


def _data_bool(data: ET.Element, name: str) -> bool:
    return _truthy(_data_text(data, name))


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _accepts_file_upload(data: ET.Element) -> bool:
    dropbox2 = first_child(data, "dropbox2")
    if dropbox2 is not None:
        try:
            type_bits = int(dropbox2.attrib.get("type", "0"))
        except ValueError:
            type_bits = 0
        file_like_mask = 0x02 | 0x04 | 0x10 | 0x20 | 0x40 | 0x80
        if type_bits & file_like_mask:
            return True

    legacy = first_child(data, "dropbox") or first_child(data, "dropbox_")
    if legacy is not None and _truthy(clean_text(legacy)):
        return True

    dropbox_type = first_child(data, "dropboxtype")
    if dropbox_type is not None:
        value = clean_text(dropbox_type).lower()
        if value in {
            "singledocument",
            "documenttemplate",
            "multipledocuments",
            "audiorecording",
        }:
            return True
    return False


def _dropbox_filetypes(data: ET.Element) -> str:
    dropbox2 = first_child(data, "dropbox2")
    if dropbox2 is None:
        return ""
    return dropbox2.attrib.get("filetypes", "") or ""


def _dropbox_multiple(data: ET.Element) -> bool:
    dropbox2 = first_child(data, "dropbox2")
    if dropbox2 is None:
        return False
    return _truthy(dropbox2.attrib.get("multiple", ""))
