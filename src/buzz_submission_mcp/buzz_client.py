from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BuzzErrorCode = Literal[
    "AUTH_REQUIRED",
    "INSUFFICIENT_BUZZ_RIGHTS",
    "NOT_FOUND",
    "RATE_LIMITED",
    "BUZZ_API_ERROR",
    "INVALID_ID",
    "UNSUPPORTED_ACTIVITY_TYPE",
    "REDACTED_FOR_PRIVACY",
]


RETRYABLE_ERROR_CODES = {"RATE_LIMITED"}


class BuzzApiError(RuntimeError):
    """Raised when Buzz returns an HTTP, authentication, or DLAP-level error."""

    def __init__(
        self,
        message: str,
        *,
        code: BuzzErrorCode = "BUZZ_API_ERROR",
        retryable: bool | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = (
            retryable if retryable is not None else code in RETRYABLE_ERROR_CODES
        )
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": str(self),
            "retryable": self.retryable,
        }
        if self.details:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class BuzzCredentials:
    username: str
    password: str
    domain: str

    @property
    def qualified_username(self) -> str:
        if "/" in self.username:
            return self.username
        return f"{self.domain}/{self.username}"

    @classmethod
    def from_env(cls) -> "BuzzCredentials":
        missing = [
            key
            for key in ("BUZZ_USERNAME", "BUZZ_PASSWORD", "BUZZ_DOMAIN")
            if not os.getenv(key)
        ]
        if missing:
            raise BuzzApiError(
                "Missing Buzz authentication environment variables: "
                + ", ".join(missing),
                code="AUTH_REQUIRED",
                details={"missing_env": missing},
            )
        return cls(
            username=os.environ["BUZZ_USERNAME"],
            password=os.environ["BUZZ_PASSWORD"],
            domain=os.environ["BUZZ_DOMAIN"],
        )


class BuzzClient:
    """Small DLAP client for the commands needed by the MCP tool."""

    DEFAULT_BASE_URL = "https://api.agilixbuzz.com"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        credentials: BuzzCredentials | None = None,
        timeout: float = 30.0,
    ) -> None:
        resolved = base_url or os.getenv("BUZZ_BASE_URL") or self.DEFAULT_BASE_URL
        self.base_url = resolved.rstrip("/")
        self.credentials = credentials or BuzzCredentials.from_env()
        self.timeout = timeout
        self._token: str | None = None

    @property
    def cmd_url(self) -> str:
        return f"{self.base_url}/cmd"

    def close(self) -> None:
        return None

    def login(self) -> str:
        request = ET.Element(
            "request",
            {
                "cmd": "login3",
                "username": self.credentials.qualified_username,
                "password": self.credentials.password,
            },
        )
        text = self._request_text(
            "Login2",
            self.cmd_url,
            method="POST",
            body=ET.tostring(request, encoding="utf-8"),
            headers={"Content-Type": "text/xml"},
        )
        root = _parse_xml(text, "Login3 response")
        _raise_for_dlap_error(root, "Login3")

        user = _first(root, "user")
        token = None
        if user is not None:
            token = user.attrib.get("token")
        token = token or root.attrib.get("_token") or root.attrib.get("token")
        if not token:
            raise BuzzApiError(
                "Login3 succeeded but no authentication token was returned.",
                code="AUTH_REQUIRED",
                details={"command": "Login3"},
            )
        self._token = token
        return token

    def get_student_submission(self, *, enrollmentid: str, itemid: str) -> str:
        params = {
            "cmd": "getstudentsubmission",
            "enrollmentid": enrollmentid,
            "itemid": itemid,
            "packagetype": "data",
        }
        return self._get_text("GetStudentSubmission", params)

    def get_item(self, *, entityid: str, itemid: str) -> str:
        params = {"cmd": "getitem", "entityid": entityid, "itemid": itemid}
        return self._get_text("GetItem", params)

    def get_item_list(self, *, entityid: str, itemid: str | None = None) -> str:
        params: dict[str, Any] = {"cmd": "getitemlist", "entityid": entityid}
        if itemid:
            params["itemid"] = itemid
        return self._get_text("GetItemList", params)

    def list_questions(
        self,
        *,
        entityid: str,
        questionids: list[str] | None = None,
        itemid: str | None = None,
    ) -> str:
        params: dict[str, Any] = {"cmd": "listquestions", "entityid": entityid}
        if questionids:
            params["questionid"] = "|".join(questionids)
        elif itemid:
            params["itemid"] = itemid
        else:
            raise BuzzApiError(
                "list_questions requires questionids or itemid to scope the request.",
                code="INVALID_ID",
                details={"command": "ListQuestions"},
            )
        return self._get_text("ListQuestions", params)

    def get_question_list(self, *, entityid: str, questionids: list[str]) -> str:
        if not questionids:
            raise BuzzApiError(
                "Cannot fetch questions because no question IDs were found.",
                code="INVALID_ID",
                details={"command": "GetQuestionList"},
            )
        params = {
            "cmd": "getquestionlist",
            "entityid": entityid,
            "questionid": "|".join(questionids),
        }
        return self._get_text("GetQuestionList", params)

    def submission_file_url(
        self,
        *,
        enrollmentid: str,
        itemid: str,
        filepath: str,
        inline: bool = True,
    ) -> str:
        """Authenticated URL for a file attached to a submitted assignment/homework/SCO."""

        return self._build_file_url(
            "getstudentsubmission",
            {
                "enrollmentid": enrollmentid,
                "itemid": itemid,
                "packagetype": "file",
                "filepath": filepath,
                "inline": "true" if inline else "false",
            },
        )

    def attempt_file_url(
        self,
        *,
        enrollmentid: str,
        itemid: str,
        partid: str,
        filepath: str,
        inline: bool = True,
    ) -> str:
        """Authenticated URL for a file uploaded to a fileupload assessment question."""

        return self._build_file_url(
            "getattemptfile",
            {
                "enrollmentid": enrollmentid,
                "itemid": itemid,
                "partid": partid,
                "filepath": filepath,
                "inline": "true" if inline else "false",
            },
        )

    def _build_file_url(self, cmd: str, params: dict[str, Any]) -> str:
        if not self._token:
            self.login()
        query = dict(params)
        query["cmd"] = cmd
        query["_token"] = self._token
        return f"{self.cmd_url}?{urlencode(query)}"

    def _get_text(self, command: str, params: dict[str, Any]) -> str:
        if not self._token:
            self.login()
        params = dict(params)
        params["_token"] = self._token
        url = f"{self.cmd_url}?{urlencode(params)}"
        text = self._request_text(command, url, method="GET")
        if text.lstrip().startswith("<"):
            root = _parse_xml(text, f"{command} response")
            _raise_for_dlap_error(root, command)
        return text

    def _request_text(
        self,
        command: str,
        url: str,
        *,
        method: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        request_headers = {
            "Accept": "application/xml",
            "User-Agent": "buzz-submission-mcp/0.1",
        }
        request_headers.update(headers or {})
        request = Request(url, data=body, headers=request_headers, method=method)
        try:
            with self._open_url(request) as response:
                text = response.read().decode(
                    response.headers.get_content_charset() or "utf-8",
                    errors="replace",
                )
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            code = _code_for_http_status(exc.code)
            raise BuzzApiError(
                f"{command} failed with HTTP {exc.code}: "
                f"{redact_secrets(error_body[:500])}",
                code=code,
                retryable=code == "RATE_LIMITED" or exc.code >= 500,
                details={"command": command, "http_status": exc.code},
            ) from exc
        except URLError as exc:
            raise BuzzApiError(
                f"{command} failed to reach Buzz: {redact_secrets(str(exc.reason))}",
                retryable=True,
                details={"command": command},
            ) from exc

        if not text.strip():
            raise BuzzApiError(
                f"{command} returned an empty payload.",
                retryable=True,
                details={"command": command},
            )
        return text

    def _open_url(self, request: Request) -> Any:
        return urlopen(request, timeout=self.timeout)


def _parse_xml(xml_text: str, label: str) -> ET.Element:
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise BuzzApiError(
            f"{label} was not valid XML: {exc}",
            details={"payload": label},
        ) from exc


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _first(root: ET.Element, name: str) -> ET.Element | None:
    wanted = name.lower()
    for element in root.iter():
        if _local_name(element.tag) == wanted:
            return element
    return None


def _raise_for_dlap_error(root: ET.Element, command: str) -> None:
    for element in root.iter():
        code = element.attrib.get("code")
        if code and code.upper() != "OK":
            message = element.attrib.get("message") or _text(element) or "No message returned."
            error_code = _code_for_dlap_error(command, code, message)
            raise BuzzApiError(
                f"{command} returned {code}: {redact_secrets(message)}",
                code=error_code,
                retryable=error_code == "RATE_LIMITED",
                details={"command": command, "dlap_code": code},
            )


def _text(element: ET.Element) -> str:
    return " ".join(part.strip() for part in element.itertext() if part and part.strip())


def _code_for_http_status(status: int) -> BuzzErrorCode:
    if status == 401:
        return "AUTH_REQUIRED"
    if status == 403:
        return "INSUFFICIENT_BUZZ_RIGHTS"
    if status == 404:
        return "NOT_FOUND"
    if status == 429:
        return "RATE_LIMITED"
    return "BUZZ_API_ERROR"


def _code_for_dlap_error(command: str, dlap_code: str, message: str) -> BuzzErrorCode:
    combined = f"{dlap_code} {message}".lower()
    if command.lower().startswith("login"):
        return "AUTH_REQUIRED"
    if any(term in combined for term in ("unauthor", "auth", "login", "token")):
        return "AUTH_REQUIRED"
    if any(
        term in combined for term in ("denied", "forbidden", "rights", "permission")
    ):
        return "INSUFFICIENT_BUZZ_RIGHTS"
    if any(term in combined for term in ("not found", "notfound", "missing")):
        return "NOT_FOUND"
    if any(term in combined for term in ("rate", "throttle", "too many")):
        return "RATE_LIMITED"
    return "BUZZ_API_ERROR"


SECRET_FIELD_NAMES = (
    "_token",
    "token",
    "password",
    "sessionid",
    "access_token",
    "refresh_token",
)


def redact_secrets(value: str) -> str:
    """Redact common Buzz credential and token shapes from diagnostic text."""

    redacted = value
    field_pattern = "|".join(re.escape(name) for name in SECRET_FIELD_NAMES)
    redacted = re.sub(
        rf"(?i)([?&](?:{field_pattern})=)[^&\s\"'<>]+",
        r"\1[REDACTED]",
        redacted,
    )
    redacted = re.sub(
        rf"(?i)(\b(?:{field_pattern})=)[^&\s\"'<>]+",
        r"\1[REDACTED]",
        redacted,
    )
    redacted = re.sub(
        rf"(?i)(\b(?:{field_pattern})\s*=\s*[\"'])[^\"']*([\"'])",
        r"\1[REDACTED]\2",
        redacted,
    )
    redacted = re.sub(
        rf"(?i)(\"(?:{field_pattern})\"\s*:\s*\")[^\"]*(\")",
        r"\1[REDACTED]\2",
        redacted,
    )
    redacted = re.sub(
        rf"(?i)(<(?:{field_pattern})>)[^<]*(</(?:{field_pattern})>)",
        r"\1[REDACTED]\2",
        redacted,
    )
    return redacted
