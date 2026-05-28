from __future__ import annotations

from typing import Any

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - compatibility with older MCP SDK layouts.
    from mcp.server.fastmcp import FastMCP

from .buzz_client import BuzzApiError, BuzzClient
from .reporting import (
    build_complete_submission_report,
    extract_question_ids,
    normalize_submission_request,
)

mcp = FastMCP("buzz-submission-reports")


@mcp.tool()
def get_complete_submission_report(
    submissionid: str | None = None,
    enrollmentid: str | None = None,
    itemid: str | None = None,
    entityid: str | None = None,
) -> dict[str, Any]:
    """Return a human-readable Buzz student submission report.

    Resolves the item/assignment/custom-activity title, maps every question's
    choice/order/match IDs into readable answer text via ListQuestions, and
    builds authenticated download URLs for any submitted attachments (e.g.
    PDFs uploaded to an assignment dropbox or to a fileupload question).
    """

    request = normalize_submission_request(
        submissionid=submissionid,
        enrollmentid=enrollmentid,
        itemid=itemid,
        entityid=entityid,
    )

    client = BuzzClient()
    try:
        submission_xml = client.get_student_submission(
            enrollmentid=request.enrollmentid,
            itemid=request.itemid,
        )
        try:
            item_xml = client.get_item(entityid=request.entityid, itemid=request.itemid)
        except BuzzApiError:
            item_xml = client.get_item_list(
                entityid=request.entityid, itemid=request.itemid
            )

        questionids = extract_question_ids(submission_xml)
        if questionids:
            try:
                question_xml = client.list_questions(
                    entityid=request.entityid, questionids=questionids
                )
            except BuzzApiError:
                question_xml = client.get_question_list(
                    entityid=request.entityid, questionids=questionids
                )
        else:
            # No question-shaped submissions (e.g. a pure dropbox assignment).
            # Synthesize an empty ListQuestions payload so extract_questions skips cleanly.
            question_xml = "<response code=\"OK\"></response>"

        return build_complete_submission_report(
            submission_xml=submission_xml,
            item_xml=item_xml,
            question_xml=question_xml,
            base_url=client.base_url,
            request=request,
            url_builder=client,
        )
    except BuzzApiError:
        raise
    except Exception as exc:
        raise BuzzApiError(f"Failed to build submission report: {exc}") from exc
    finally:
        client.close()


if __name__ == "__main__":
    mcp.run()
