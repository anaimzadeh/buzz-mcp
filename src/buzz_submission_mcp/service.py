from __future__ import annotations

from typing import Any, Callable, Literal, Protocol

from .buzz_client import BuzzApiError, BuzzClient
from .entities import extract_course, extract_enrollment, extract_enrollments
from .reporting import (
    ItemInfo,
    SubmissionRequest,
    build_complete_submission_report,
    extract_item_info,
    extract_item_infos,
    extract_question_ids,
    normalize_submission_request,
)


class BuzzReadClient(Protocol):
    base_url: str

    def close(self) -> None: ...
    def get_student_submission(self, *, enrollmentid: str, itemid: str) -> str: ...
    def get_item(self, *, entityid: str, itemid: str) -> str: ...
    def get_item_list(self, *, entityid: str, itemid: str | None = None) -> str: ...
    def get_course(self, *, courseid: str, version: str | None = None) -> str: ...
    def get_enrollment(self, *, enrollmentid: str) -> str: ...
    def list_user_enrollments(
        self,
        *,
        userid: str,
        entityid: str | None = None,
        allstatus: bool = False,
    ) -> str: ...
    def list_entity_enrollments(
        self,
        *,
        entityid: str,
        userid: str | None = None,
        allstatus: bool = False,
    ) -> str: ...
    def list_questions(
        self,
        *,
        entityid: str,
        questionids: list[str] | None = None,
        itemid: str | None = None,
    ) -> str: ...
    def get_question_list(self, *, entityid: str, questionids: list[str]) -> str: ...
    def submission_file_url(
        self, *, enrollmentid: str, itemid: str, filepath: str, inline: bool = True
    ) -> str: ...
    def attempt_file_url(
        self,
        *,
        enrollmentid: str,
        itemid: str,
        partid: str,
        filepath: str,
        inline: bool = True,
    ) -> str: ...


class BuzzReadService:
    """Read-only Buzz workflows exposed through the MCP server."""

    def __init__(
        self, client_factory: Callable[[], BuzzReadClient] | None = None
    ) -> None:
        self._client_factory = client_factory or BuzzClient

    def get_activity(self, *, entityid: str, itemid: str) -> dict[str, Any]:
        client = self._client_factory()
        try:
            item_xml = self._get_item_xml(client, entityid=entityid, itemid=itemid)
            return activity_to_dict(extract_item_info(item_xml), entityid=entityid)
        finally:
            client.close()

    def list_activities(self, *, entityid: str) -> dict[str, Any]:
        client = self._client_factory()
        try:
            item_xml = client.get_item_list(entityid=entityid)
            activities = [
                activity_to_dict(item, entityid=entityid)
                for item in extract_item_infos(item_xml)
            ]
            return {
                "entityid": entityid,
                "count": len(activities),
                "activities": activities,
            }
        finally:
            client.close()

    def get_course(
        self, *, courseid: str, version: str | None = None
    ) -> dict[str, Any]:
        client = self._client_factory()
        try:
            course_xml = client.get_course(courseid=courseid, version=version)
            return extract_course(course_xml)
        finally:
            client.close()

    def get_enrollment(self, *, enrollmentid: str) -> dict[str, Any]:
        client = self._client_factory()
        try:
            enrollment_xml = client.get_enrollment(enrollmentid=enrollmentid)
            return extract_enrollment(enrollment_xml)
        finally:
            client.close()

    def list_user_enrollments(
        self,
        *,
        userid: str,
        entityid: str | None = None,
        allstatus: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        limit = _validated_limit(limit)
        client = self._client_factory()
        try:
            enrollments_xml = client.list_user_enrollments(
                userid=userid,
                entityid=entityid,
                allstatus=allstatus,
            )
            enrollments = extract_enrollments(enrollments_xml)[:limit]
            payload: dict[str, Any] = {
                "userid": userid,
                "count": len(enrollments),
                "limit": limit,
                "enrollments": enrollments,
            }
            if entityid:
                payload["entityid"] = entityid
            return payload
        finally:
            client.close()

    def list_entity_enrollments(
        self,
        *,
        entityid: str,
        userid: str | None = None,
        allstatus: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        limit = _validated_limit(limit)
        client = self._client_factory()
        try:
            enrollments_xml = client.list_entity_enrollments(
                entityid=entityid,
                userid=userid,
                allstatus=allstatus,
            )
            enrollments = extract_enrollments(enrollments_xml)[:limit]
            payload: dict[str, Any] = {
                "entityid": entityid,
                "count": len(enrollments),
                "limit": limit,
                "enrollments": enrollments,
            }
            if userid:
                payload["userid"] = userid
            return payload
        finally:
            client.close()

    def get_submission_report(
        self,
        *,
        submissionid: str | None = None,
        enrollmentid: str | None = None,
        itemid: str | None = None,
        entityid: str | None = None,
    ) -> dict[str, Any]:
        request = normalize_submission_request(
            submissionid=submissionid,
            enrollmentid=enrollmentid,
            itemid=itemid,
            entityid=entityid,
        )

        client = self._client_factory()
        try:
            submission_xml = client.get_student_submission(
                enrollmentid=request.enrollmentid,
                itemid=request.itemid,
            )
            item_xml = self._get_item_xml(
                client, entityid=request.entityid, itemid=request.itemid
            )
            question_xml = self._get_question_xml(client, request, submission_xml)
            return build_complete_submission_report(
                submission_xml=submission_xml,
                item_xml=item_xml,
                question_xml=question_xml,
                base_url=client.base_url,
                request=request,
                url_builder=client,
            )
        finally:
            client.close()

    def get_attachment_url(
        self,
        *,
        enrollmentid: str,
        itemid: str,
        filepath: str,
        source: Literal["submission", "attempt-question"] = "submission",
        partid: str | None = None,
    ) -> dict[str, Any]:
        if source not in {"submission", "attempt-question"}:
            raise BuzzApiError(
                "source must be 'submission' or 'attempt-question'.",
                code="INVALID_ID",
                details={"field": "source"},
            )
        if source == "attempt-question" and not partid:
            raise BuzzApiError(
                "partid is required when source is 'attempt-question'.",
                code="INVALID_ID",
                details={"field": "partid"},
            )

        client = self._client_factory()
        try:
            if source == "attempt-question":
                assert partid is not None
                url = client.attempt_file_url(
                    enrollmentid=enrollmentid,
                    itemid=itemid,
                    partid=partid,
                    filepath=filepath,
                )
            else:
                url = client.submission_file_url(
                    enrollmentid=enrollmentid,
                    itemid=itemid,
                    filepath=filepath,
                )
        finally:
            client.close()

        payload = {"download_url": url, "source": source, "filepath": filepath}
        if partid:
            payload["partid"] = partid
        return payload

    def _get_item_xml(
        self, client: BuzzReadClient, *, entityid: str, itemid: str
    ) -> str:
        try:
            return client.get_item(entityid=entityid, itemid=itemid)
        except BuzzApiError as exc:
            if exc.code in {
                "AUTH_REQUIRED",
                "INSUFFICIENT_BUZZ_RIGHTS",
                "RATE_LIMITED",
            }:
                raise
            return client.get_item_list(entityid=entityid, itemid=itemid)

    def _get_question_xml(
        self, client: BuzzReadClient, request: SubmissionRequest, submission_xml: str
    ) -> str:
        questionids = extract_question_ids(submission_xml)
        if not questionids:
            return "<response code=\"OK\"></response>"
        try:
            return client.list_questions(
                entityid=request.entityid, questionids=questionids
            )
        except BuzzApiError as exc:
            if exc.code in {
                "AUTH_REQUIRED",
                "INSUFFICIENT_BUZZ_RIGHTS",
                "RATE_LIMITED",
            }:
                raise
            return client.get_question_list(
                entityid=request.entityid, questionids=questionids
            )


def activity_to_dict(item: ItemInfo, *, entityid: str | None = None) -> dict[str, Any]:
    activity = {
        "id": item.itemid,
        "title": item.title,
        "type": item.item_type,
        "abbreviation": item.abbreviation,
        "accepts_file_upload": item.accepts_file_upload,
        "allowed_filetypes": item.allowed_filetypes,
        "dropbox_multiple": item.dropbox_multiple,
        "perfect_score": item.perfect_score,
        "due_date": item.duedate,
    }
    if entityid is not None:
        activity["entityid"] = entityid
    return activity


def _validated_limit(limit: int) -> int:
    if limit < 1 or limit > 100:
        raise BuzzApiError(
            "limit must be between 1 and 100.",
            code="INVALID_ID",
            details={"field": "limit", "minimum": 1, "maximum": 100},
        )
    return limit
