from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from .buzz_client import BuzzApiError


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubmissionRequest:
    enrollmentid: str
    itemid: str
    entityid: str


@dataclass(frozen=True)
class Attachment:
    """A file (often a PDF) attached to a submission or fileupload question."""

    name: str
    path: str
    attachment_type: str
    source: str  # "submission" or "attempt-question"
    questionid: str | None = None
    partid: str | None = None
    download_url: str | None = None


@dataclass(frozen=True)
class AnswerRecord:
    questionid: str
    answer: str
    answer_source: str
    partid: str | None = None
    attachments: tuple[Attachment, ...] = ()


@dataclass(frozen=True)
class QuestionInfo:
    questionid: str
    body: str
    interaction_type: str | None
    choices: dict[str, str]
    correct_choice_answers: dict[str, str]  # for match: choice id -> correct answer text
    correct_values: tuple[str, ...]


@dataclass(frozen=True)
class ItemInfo:
    itemid: str
    title: str
    item_type: str
    abbreviation: str
    accepts_file_upload: bool
    allowed_filetypes: str
    dropbox_multiple: bool
    perfect_score: str
    duedate: str

    @property
    def is_custom_activity(self) -> bool:
        return self.item_type.lower() == "customactivity"

    @property
    def is_assignment(self) -> bool:
        return self.item_type.lower() == "assignment"


class FileUrlBuilder(Protocol):
    def submission_file_url(self, *, enrollmentid: str, itemid: str, filepath: str, inline: bool = True) -> str: ...
    def attempt_file_url(self, *, enrollmentid: str, itemid: str, partid: str, filepath: str, inline: bool = True) -> str: ...


# ---------------------------------------------------------------------------
# Request normalization
# ---------------------------------------------------------------------------


def normalize_submission_request(
    *,
    submissionid: str | None = None,
    enrollmentid: str | None = None,
    itemid: str | None = None,
    entityid: str | None = None,
) -> SubmissionRequest:
    """Accept explicit Buzz IDs or a convenience encoded submissionid."""

    payload: dict[str, Any] = {}
    if submissionid:
        payload = _parse_submissionid(submissionid)

    enrollmentid = enrollmentid or payload.get("enrollmentid") or payload.get("enrollment_id")
    itemid = itemid or payload.get("itemid") or payload.get("item_id")
    entityid = (
        entityid
        or payload.get("entityid")
        or payload.get("entity_id")
        or payload.get("courseid")
        or payload.get("course_id")
    )

    missing = [
        name
        for name, value in {
            "enrollmentid": enrollmentid,
            "itemid": itemid,
            "entityid": entityid,
        }.items()
        if not value
    ]
    if missing:
        raise BuzzApiError(
            "Missing required Buzz ID(s): "
            + ", ".join(missing)
            + ". GetStudentSubmission uses enrollmentid and itemid; "
            "GetItemList/ListQuestions also need entityid.",
            code="INVALID_ID",
            details={"missing_ids": missing},
        )

    return SubmissionRequest(
        enrollmentid=str(enrollmentid),
        itemid=str(itemid),
        entityid=str(entityid),
    )


# ---------------------------------------------------------------------------
# Top-level report assembly
# ---------------------------------------------------------------------------


def build_complete_submission_report(
    *,
    submission_xml: str,
    item_xml: str,
    question_xml: str,
    base_url: str,
    request: SubmissionRequest | None = None,
    url_builder: FileUrlBuilder | None = None,
) -> dict[str, Any]:
    """Render a human-readable JSON report for a Buzz student submission.

    Resolves item/activity name, top-level submission attachments (e.g. uploaded
    PDFs), and per-question answers — mapping choice/order/match IDs into their
    answer text via GetQuestionList/ListQuestions data.
    """

    item = extract_item_info(item_xml)
    questions = extract_questions(question_xml)
    submission_root = parse_xml(submission_xml, "GetStudentSubmission payload")

    top_attachments = _extract_top_level_attachments(submission_root)
    answer_records = _collect_answer_records(submission_root)

    top_attachments = tuple(
        _with_submission_url(att, request=request, url_builder=url_builder, base_url=base_url)
        for att in top_attachments
    )
    answer_records = tuple(
        _enrich_record_attachments(
            record,
            request=request,
            url_builder=url_builder,
            base_url=base_url,
        )
        for record in answer_records
    )

    q_and_a_pairs: list[dict[str, Any]] = []
    for record in answer_records:
        question = questions.get(record.questionid)
        question_text = question.body if question else f"Unknown question {record.questionid}"
        answer_text = humanize_answer(record, question)
        pair: dict[str, Any] = {
            "question": question_text,
            "answer": answer_text,
        }
        if question and question.interaction_type:
            pair["interaction_type"] = question.interaction_type
        if record.attachments:
            pair["attachments"] = [_attachment_to_dict(a) for a in record.attachments]
        q_and_a_pairs.append(pair)

    return {
        "activity_title": item.title,
        "activity": {
            "id": item.itemid,
            "title": item.title,
            "type": item.item_type,
            "abbreviation": item.abbreviation,
            "accepts_file_upload": item.accepts_file_upload,
            "allowed_filetypes": item.allowed_filetypes,
            "dropbox_multiple": item.dropbox_multiple,
            "perfect_score": item.perfect_score,
            "due_date": item.duedate,
        },
        "student_attachments": [_attachment_to_dict(a) for a in top_attachments],
        "q_and_a_pairs": q_and_a_pairs,
    }


# ---------------------------------------------------------------------------
# Item / activity name resolution
# ---------------------------------------------------------------------------


def extract_item_info(item_xml: str) -> ItemInfo:
    root = parse_xml(item_xml, "GetItem/GetItemList payload")
    item_element = _find_item_element(root)
    if item_element is None:
        raise BuzzApiError(
            "Response did not include an <item> element to resolve the activity name.",
            code="NOT_FOUND",
        )

    data = first_child(item_element, "data")
    if data is None:
        raise BuzzApiError(
            "Item response missing <data> block; cannot resolve title/type.",
            details={"parser": "extract_item_info"},
        )

    itemid = item_element.attrib.get("id") or item_element.attrib.get("itemid") or ""
    title = _data_text(data, "title")
    if not title:
        raise BuzzApiError(
            "Item <data> did not include a <title> value.",
            details={"parser": "extract_item_info"},
        )

    return ItemInfo(
        itemid=itemid,
        title=title,
        item_type=_data_text(data, "type"),
        abbreviation=_data_text(data, "abbreviation"),
        accepts_file_upload=_accepts_file_upload(data),
        allowed_filetypes=_dropbox_filetypes(data),
        dropbox_multiple=_dropbox_multiple(data),
        perfect_score=_data_text(data, "perfectscore") or _data_text(data, "perfectscore_"),
        duedate=_data_text(data, "duedate"),
    )


def extract_activity_title(item_xml: str) -> str:
    """Backwards-compatible shortcut used by older callers and tests."""

    return extract_item_info(item_xml).title


def _find_item_element(root: ET.Element) -> ET.Element | None:
    for element in root.iter():
        if local_name(element.tag) == "item" and first_child(element, "data") is not None:
            return element
    return None


def _data_text(data: ET.Element, name: str) -> str:
    # Buzz returns some attribute-like values with a trailing underscore (e.g. perfectscore_).
    primary = first_child(data, name)
    if primary is None:
        primary = first_child(data, f"{name}_")
    return clean_text(primary)


# `<dropbox2 type="2" multiple="true" filetypes=".pdf"/>` indicates submission uploads.
def _accepts_file_upload(data: ET.Element) -> bool:
    dropbox2 = first_child(data, "dropbox2")
    if dropbox2 is not None:
        try:
            type_bits = int(dropbox2.attrib.get("type", "0"))
        except ValueError:
            type_bits = 0
        # DropboxElement bitmask: File=0x02 GoogleFile=0x04 Template=0x08 Image=0x10
        # Drawing=0x20 Audio=0x40 Video=0x80 Url=0x100.
        file_like_mask = 0x02 | 0x04 | 0x10 | 0x20 | 0x40 | 0x80
        if type_bits & file_like_mask:
            return True
    legacy = first_child(data, "dropbox") or first_child(data, "dropbox_")
    if legacy is not None and (clean_text(legacy) or "").lower() in {"true", "1"}:
        return True
    dropbox_type = first_child(data, "dropboxtype")
    if dropbox_type is not None:
        value = clean_text(dropbox_type).lower()
        if value in {"singledocument", "documenttemplate", "multipledocuments", "audiorecording"}:
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
    return (dropbox2.attrib.get("multiple") or "").lower() == "true"


# ---------------------------------------------------------------------------
# Question / answer mapping
# ---------------------------------------------------------------------------


def extract_questions(question_xml: str) -> dict[str, QuestionInfo]:
    root = parse_xml(question_xml, "ListQuestions/GetQuestionList payload")
    questions: dict[str, QuestionInfo] = {}
    for element in root.iter():
        if local_name(element.tag) != "question":
            continue
        questionid = (
            element.attrib.get("questionid")
            or element.attrib.get("id")
            or element.attrib.get("partid")
        )
        if not questionid:
            continue
        body = clean_text(first_child(element, "body")) or f"Question {questionid}"
        interaction = first_child(element, "interaction")
        interaction_type = interaction.attrib.get("type") if interaction is not None else None
        choices: dict[str, str] = {}
        correct_choice_answers: dict[str, str] = {}
        if interaction is not None:
            for choice in direct_children(interaction, "choice"):
                choice_id = choice.attrib.get("id")
                if not choice_id:
                    continue
                choice_body = clean_text(first_child(choice, "body")) or clean_text(choice)
                if choice_body:
                    choices[choice_id] = choice_body
                # Match-type questions store correct counterpart text inside the choice.
                choice_answer = clean_text(first_child(choice, "answer"))
                if choice_answer:
                    correct_choice_answers[choice_id] = choice_answer
        correct_values: list[str] = []
        answer_element = first_child(element, "answer")
        if answer_element is not None:
            for value in direct_children(answer_element, "value"):
                v = clean_text(value)
                if v:
                    correct_values.append(v)
        questions[questionid] = QuestionInfo(
            questionid=questionid,
            body=body,
            interaction_type=interaction_type,
            choices=choices,
            correct_choice_answers=correct_choice_answers,
            correct_values=tuple(correct_values),
        )
    return questions


def humanize_answer(record: AnswerRecord, question: QuestionInfo | None) -> str:
    raw_answer = (record.answer or "").strip()
    if not raw_answer and not record.attachments:
        return ""

    if record.attachments and not raw_answer:
        return ", ".join(a.download_url or a.path for a in record.attachments)

    interaction = (question.interaction_type or "").lower() if question else ""

    if interaction in {"choice", "answer"} and question and question.choices:
        ids = _split_answer_tokens(raw_answer)
        labels = [question.choices.get(v, v) for v in ids]
        return ", ".join(labels)

    if interaction == "order" and question and question.choices:
        ids = _split_answer_tokens(raw_answer)
        labels = [question.choices.get(v, v) for v in ids]
        return " → ".join(labels)

    if interaction == "match" and question and question.choices:
        return _humanize_match_answer(raw_answer, question)

    if interaction == "text":
        return raw_answer

    if interaction == "fileupload":
        if record.attachments:
            return ", ".join(a.download_url or a.path for a in record.attachments)
        return raw_answer

    return raw_answer


def _split_answer_tokens(value: str) -> list[str]:
    parts: list[str] = []
    for chunk in re.split(r"[,;|]", value):
        token = chunk.strip()
        if token:
            parts.append(token)
    return parts


def _humanize_match_answer(raw_answer: str, question: QuestionInfo) -> str:
    pairs: list[str] = []
    tokens = _split_answer_tokens(raw_answer)
    for index, token in enumerate(tokens):
        if "=" in token:
            left, right = token.split("=", 1)
            left = left.strip()
            right = right.strip()
            prompt = question.choices.get(left, left)
            response = question.choices.get(right, right) or question.correct_choice_answers.get(left, right)
            pairs.append(f"{prompt} → {response}")
            continue
        # Positional answer: index i pairs with the i-th choice's prompt.
        choice_ids = list(question.choices.keys())
        if index < len(choice_ids):
            prompt_id = choice_ids[index]
            prompt = question.choices.get(prompt_id, prompt_id)
            response = question.choices.get(token, token) or question.correct_choice_answers.get(prompt_id, token)
            pairs.append(f"{prompt} → {response}")
        else:
            pairs.append(token)
    return ", ".join(pairs)


def extract_question_ids(submission_xml: str) -> list[str]:
    root = parse_xml(submission_xml, "GetStudentSubmission payload")
    seen: set[str] = set()
    ids: list[str] = []
    for record in _collect_answer_records(root):
        if record.questionid and record.questionid not in seen:
            seen.add(record.questionid)
            ids.append(record.questionid)
    return ids


def flatten_submission_answers(submission_xml: str) -> list[AnswerRecord]:
    root = parse_xml(submission_xml, "GetStudentSubmission payload")
    records = _collect_answer_records(root)
    if not records:
        raise BuzzApiError(
            "No question answers were found in the submission XML. "
            "Expected nested <submission type=\"question\"> nodes.",
            code="INVALID_ID",
        )
    return list(records)


# ---------------------------------------------------------------------------
# Submission XML traversal
# ---------------------------------------------------------------------------


def _extract_top_level_attachments(submission_root: ET.Element) -> tuple[Attachment, ...]:
    """Attachments on the outermost <submission> (assignment/homework/SCO uploads)."""

    target = submission_root
    if local_name(submission_root.tag) != "submission":
        for child in submission_root.iter():
            if local_name(child.tag) == "submission":
                target = child
                break
    attachments_node = first_child(target, "attachments")
    if attachments_node is None:
        return ()
    return tuple(_attachments_from(attachments_node, source="submission"))


def _collect_answer_records(submission_root: ET.Element) -> tuple[AnswerRecord, ...]:
    records: list[AnswerRecord] = []
    _walk_submission(submission_root, records)
    return tuple(records)


def _walk_submission(element: ET.Element, records: list[AnswerRecord]) -> None:
    if local_name(element.tag) == "submission" and element.attrib.get("type") == "question":
        record = _record_from_question_submission(element)
        if record is not None:
            records.append(record)
    for child in element:
        _walk_submission(child, records)


def _record_from_question_submission(element: ET.Element) -> AnswerRecord | None:
    questionid = _question_id_for_submission(element)
    if not questionid:
        return None
    partid = element.attrib.get("partid")
    answer_element = first_child(element, "answer")
    notes_element = first_child(element, "notes")
    attachments_element = first_child(element, "attachments")
    attachments = (
        tuple(_attachments_from(attachments_element, source="attempt-question", partid=partid, questionid=questionid))
        if attachments_element is not None
        else ()
    )

    answer_text = ""
    answer_source = ""
    if answer_element is not None and clean_text(answer_element):
        answer_text = clean_text(answer_element)
        answer_source = "answer"
    elif notes_element is not None and clean_text(notes_element):
        answer_text = clean_text(notes_element)
        answer_source = "notes"
    elif attachments:
        answer_source = "attachment"

    if not answer_text and not attachments:
        return None

    return AnswerRecord(
        questionid=questionid,
        answer=answer_text,
        answer_source=answer_source or "attachment",
        partid=partid,
        attachments=attachments,
    )


def _attachments_from(
    attachments_element: ET.Element,
    *,
    source: str,
    partid: str | None = None,
    questionid: str | None = None,
) -> list[Attachment]:
    result: list[Attachment] = []
    for child in direct_children(attachments_element, "attachment"):
        path = child.attrib.get("path") or clean_text(child)
        if not path:
            continue
        name = child.attrib.get("name") or _filename_from_path(path)
        result.append(
            Attachment(
                name=name,
                path=path,
                attachment_type=child.attrib.get("type", "file"),
                source=source,
                partid=partid,
                questionid=questionid,
            )
        )
    return result


def _filename_from_path(path: str) -> str:
    if "/" in path:
        return path.rsplit("/", 1)[-1]
    if "\\" in path:
        return path.rsplit("\\", 1)[-1]
    return path


def _question_id_for_submission(submission: ET.Element) -> str | None:
    # Prefer the explicit Question ID carried by <attemptquestion>, since
    # the parent <submission partid="..."> attribute often holds an
    # assessment part ID (e.g. "5") rather than the question's own ID.
    attempt_question = first_child(submission, "attemptquestion")
    if attempt_question is not None:
        for key in ("questionid", "id", "partid"):
            if attempt_question.attrib.get(key):
                return attempt_question.attrib[key]
        nested = first_child(attempt_question, "question")
        if nested is not None:
            for key in ("questionid", "id"):
                if nested.attrib.get(key):
                    return nested.attrib[key]

    for key in ("questionid", "question", "id"):
        if submission.attrib.get(key):
            return submission.attrib[key]
    # Last resort — only fall back to the submission's partid when nothing
    # else identifies the question.
    return submission.attrib.get("partid")


# ---------------------------------------------------------------------------
# Attachment URL resolution
# ---------------------------------------------------------------------------


def _attachment_to_dict(attachment: Attachment) -> dict[str, Any]:
    payload = {
        "name": attachment.name,
        "path": attachment.path,
        "type": attachment.attachment_type,
        "source": attachment.source,
    }
    if attachment.questionid:
        payload["questionid"] = attachment.questionid
    if attachment.partid:
        payload["partid"] = attachment.partid
    if attachment.download_url:
        payload["download_url"] = attachment.download_url
    return payload


def _with_submission_url(
    attachment: Attachment,
    *,
    request: SubmissionRequest | None,
    url_builder: FileUrlBuilder | None,
    base_url: str,
) -> Attachment:
    if attachment.attachment_type == "googledrivedoc":
        return _replace_attachment(attachment, download_url=attachment.path)
    if not request:
        return _replace_attachment(
            attachment,
            download_url=_fallback_static_url(base_url, attachment.path),
        )
    if url_builder is not None:
        url = url_builder.submission_file_url(
            enrollmentid=request.enrollmentid,
            itemid=request.itemid,
            filepath=attachment.path,
        )
    else:
        url = _build_submission_cmd_url(
            base_url, request.enrollmentid, request.itemid, attachment.path
        )
    return _replace_attachment(attachment, download_url=url)


def _enrich_record_attachments(
    record: AnswerRecord,
    *,
    request: SubmissionRequest | None,
    url_builder: FileUrlBuilder | None,
    base_url: str,
) -> AnswerRecord:
    if not record.attachments:
        return record
    enriched: list[Attachment] = []
    for attachment in record.attachments:
        enriched.append(
            _with_question_url(
                attachment,
                record=record,
                request=request,
                url_builder=url_builder,
                base_url=base_url,
            )
        )
    return AnswerRecord(
        questionid=record.questionid,
        answer=record.answer,
        answer_source=record.answer_source,
        partid=record.partid,
        attachments=tuple(enriched),
    )


def _with_question_url(
    attachment: Attachment,
    *,
    record: AnswerRecord,
    request: SubmissionRequest | None,
    url_builder: FileUrlBuilder | None,
    base_url: str,
) -> Attachment:
    if attachment.attachment_type == "googledrivedoc":
        return _replace_attachment(attachment, download_url=attachment.path)
    if not request or not record.partid:
        return _replace_attachment(
            attachment,
            download_url=_fallback_static_url(base_url, attachment.path),
        )
    if url_builder is not None:
        url = url_builder.attempt_file_url(
            enrollmentid=request.enrollmentid,
            itemid=request.itemid,
            partid=record.partid,
            filepath=attachment.path,
        )
    else:
        url = _build_attempt_cmd_url(
            base_url, request.enrollmentid, request.itemid, record.partid, attachment.path
        )
    return _replace_attachment(attachment, download_url=url)


def _replace_attachment(attachment: Attachment, **changes: Any) -> Attachment:
    return Attachment(
        name=changes.get("name", attachment.name),
        path=changes.get("path", attachment.path),
        attachment_type=changes.get("attachment_type", attachment.attachment_type),
        source=changes.get("source", attachment.source),
        questionid=changes.get("questionid", attachment.questionid),
        partid=changes.get("partid", attachment.partid),
        download_url=changes.get("download_url", attachment.download_url),
    )


def _fallback_static_url(base_url: str, path: str) -> str:
    normalized = path.lstrip("/")
    return f"{base_url.rstrip('/')}/{normalized}"


def _build_submission_cmd_url(
    base_url: str, enrollmentid: str, itemid: str, filepath: str
) -> str:
    from urllib.parse import urlencode

    params = urlencode(
        {
            "cmd": "getstudentsubmission",
            "enrollmentid": enrollmentid,
            "itemid": itemid,
            "packagetype": "file",
            "filepath": filepath,
            "inline": "true",
        }
    )
    return f"{base_url.rstrip('/')}/cmd?{params}"


def _build_attempt_cmd_url(
    base_url: str, enrollmentid: str, itemid: str, partid: str, filepath: str
) -> str:
    from urllib.parse import urlencode

    params = urlencode(
        {
            "cmd": "getattemptfile",
            "enrollmentid": enrollmentid,
            "itemid": itemid,
            "partid": partid,
            "filepath": filepath,
            "inline": "true",
        }
    )
    return f"{base_url.rstrip('/')}/cmd?{params}"


# Older helper retained for tests and backward compatibility.
def build_submission_file_url(base_url: str, path: str) -> str:
    return _fallback_static_url(base_url, path)


def looks_like_file_path(value: str) -> bool:
    if re.match(r"^https?://", value, re.IGNORECASE):
        return False
    return bool(re.search(r"\.[A-Za-z0-9]{2,8}$", value) or "/" in value)


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def parse_xml(xml_text: str, label: str) -> ET.Element:
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise BuzzApiError(
            f"{label} was not valid XML: {exc}",
            details={"payload": label},
        ) from exc


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def first_child(element: ET.Element | None, name: str) -> ET.Element | None:
    if element is None:
        return None
    wanted = name.lower()
    for child in element:
        if local_name(child.tag) == wanted:
            return child
    return None


def direct_children(element: ET.Element, name: str) -> list[ET.Element]:
    wanted = name.lower()
    return [child for child in element if local_name(child.tag) == wanted]


def clean_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    text = " ".join(part.strip() for part in element.itertext() if part and part.strip())
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# submissionid parsing
# ---------------------------------------------------------------------------


def _parse_submissionid(submissionid: str) -> dict[str, str]:
    value = submissionid.strip()
    if not value:
        return {}
    if value.startswith("{"):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise BuzzApiError(
                f"submissionid looked like JSON but could not be parsed: {exc}",
                code="INVALID_ID",
            ) from exc
        if not isinstance(decoded, dict):
            raise BuzzApiError(
                "submissionid JSON must be an object.",
                code="INVALID_ID",
            )
        return {str(key).lower(): str(val) for key, val in decoded.items() if val is not None}

    if ":" in value:
        parts = value.split(":")
        if len(parts) not in {2, 3}:
            raise BuzzApiError(
                "Colon-form submissionid must be enrollmentid:itemid or enrollmentid:itemid:entityid.",
                code="INVALID_ID",
            )
        keys = ["enrollmentid", "itemid", "entityid"]
        return dict(zip(keys, parts))

    return {"submissionid": value}
