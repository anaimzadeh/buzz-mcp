# Agilix Buzz MCP

<!-- mcp-name: io.github.anaimzadeh/agilix-buzz-mcp -->

FastMCP server proof of concept for an official-quality Agilix Buzz MCP.
The current read-only surface turns Buzz student submissions into
human-readable JSON reports — activity names resolved from item IDs, answers
resolved from question/choice IDs, and authenticated download URLs for submitted
PDFs or other attachments.

The spec-driven roadmap lives in [`docs/specs`](docs/specs).

## Environment

```bash
export BUZZ_USERNAME="teacher"
export BUZZ_PASSWORD="secret"
export BUZZ_DOMAIN="myschool"
# Optional — defaults to https://api.agilixbuzz.com
export BUZZ_BASE_URL="https://api.agilixbuzz.com/"
```

## Run

```bash
python -m buzz_submission_mcp.server
```

After installing the package, the same STDIO server is available as:

```bash
agilix-buzz-mcp
# or
buzz-mcp
```

## Docker

Build a local STDIO image:

```bash
docker build -t agilix-buzz-mcp:local .
```

Run it with Buzz credentials passed through the environment:

```bash
docker run --rm -i \
  -e BUZZ_USERNAME \
  -e BUZZ_PASSWORD \
  -e BUZZ_DOMAIN \
  -e BUZZ_BASE_URL \
  agilix-buzz-mcp:local
```

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

CI runs the same skipped-by-default test suite, builds the Python package, and
builds the Docker image on pushes to `main` and pull requests. It also runs an
MCP Inspector smoke test against the local STDIO server:

```bash
python scripts/mcp_inspector_smoke.py
```

The smoke script requires Node.js 22 or newer for the pinned Inspector CLI.

Live Buzz sandbox tests are opt-in and skipped by default. To run them, set
credentials plus a known-safe sandbox submission:

```bash
export BUZZ_RUN_LIVE_TESTS=1
export BUZZ_USERNAME="teacher"
export BUZZ_PASSWORD="secret"
export BUZZ_DOMAIN="myschool"
export BUZZ_TEST_ENTITYID="4378"
export BUZZ_TEST_ITEMID="assign12"
export BUZZ_TEST_ENROLLMENTID="4317"
# Optional: validates course discovery if caller has ReadCourse rights.
export BUZZ_TEST_DOMAINID="100"
# Optional: validates direct submission attachment URL generation.
export BUZZ_TEST_ATTACHMENT_FILEPATH="MyPaper.pdf"
# Optional: validates privacy-redacted user metadata if caller has ReadUser rights.
export BUZZ_TEST_USERID="9001"

PYTHONPATH=src python -m unittest tests.test_live_buzz
```

`BUZZ_TEST_DOMAINID`, `BUZZ_TEST_ATTACHMENT_FILEPATH`, and `BUZZ_TEST_USERID`
are optional and enable course discovery, direct attachment URL, and user
metadata contract coverage.

For the release gate, configure the GitHub environment `buzz-sandbox` with
these secrets:

```text
BUZZ_USERNAME
BUZZ_PASSWORD
BUZZ_DOMAIN
BUZZ_TEST_ENTITYID
BUZZ_TEST_ITEMID
BUZZ_TEST_ENROLLMENTID
```

Set the environment variable `BUZZ_TEST_SANDBOX_ACK=1` to confirm that the
target tenant and submission are safe for live validation. `BUZZ_BASE_URL`,
`BUZZ_TEST_DOMAINID`, `BUZZ_TEST_ATTACHMENT_FILEPATH`, and `BUZZ_TEST_USERID`
are optional secrets. Then run the
`Live Buzz Sandbox` workflow manually from GitHub Actions.

## PoC Tools

The preferred tool names use the `buzz.` namespace:

| Tool | Purpose |
| --- | --- |
| `buzz.get_activity` | Return normalized metadata for a Buzz activity item. |
| `buzz.get_item` | Return richer normalized metadata for a Buzz course content item. |
| `buzz.list_items` | Return a bounded list of normalized Buzz course content items. |
| `buzz.list_activities` | Return normalized metadata for every activity item in a Buzz course. |
| `buzz.get_manifest` | Return a bounded, depth-first summary of a Buzz course content manifest. |
| `buzz.get_course` | Return normalized metadata for a Buzz course or course-like entity. |
| `buzz.list_courses` | Return normalized course records for an explicit Buzz domain. |
| `buzz.get_user` | Return privacy-redacted metadata for a Buzz user. |
| `buzz.get_enrollment` | Return a normalized Buzz enrollment record. |
| `buzz.list_user_enrollments` | Return normalized enrollment records for a user. |
| `buzz.list_entity_enrollments` | Return normalized enrollment records for a course/entity. |
| `buzz.get_submission_report` | Return a human-readable submission report. |
| `buzz.get_attachment_url` | Build an authenticated URL for a known submission attachment path. |
| `buzz.docs.search` | Search the local high-value Buzz documentation catalog. |
| `buzz.docs.get_command` | Return local metadata for a known Buzz command. |
| `buzz.docs.get_schema` | Return local metadata for a known Buzz schema. |
| `get_complete_submission_report` | Backward-compatible alias for `buzz.get_submission_report`. |

The `buzz.docs.*` tools are local metadata helpers and do not require Buzz
credentials.

## Resources

The PoC exposes read-only resource templates:

```text
buzz://course/{entityid}/manifest
buzz://course/{entityid}/manifest/summary
buzz://course/{entityid}/items
buzz://course/{entityid}/item/{itemid}
buzz://course/{entityid}
buzz://domain/{domainid}/courses
buzz://user/{userid}
buzz://enrollment/{enrollmentid}
buzz://user/{userid}/enrollments
buzz://course/{entityid}/enrollments
buzz://submission/{enrollmentid}/{itemid}/report{?entityid}
```

## Prompts

The PoC includes prompt templates for common workflows:

```text
buzz.summarize_submission
buzz.draft_student_feedback
buzz.troubleshoot_submission_access
```

## Submission Report Tool

`buzz.get_submission_report` and `get_complete_submission_report` accept
explicit IDs:

```json
{
  "enrollmentid": "4317",
  "itemid": "assign12",
  "entityid": "4378"
}
```

…or a convenience `submissionid` as JSON or colon-separated text:

```json
{"submissionid": "{\"enrollmentid\":\"4317\",\"itemid\":\"assign12\",\"entityid\":\"4378\"}"}
```

```json
{"submissionid": "4317:assign12:4378"}
```

It returns:

```json
{
  "activity_title": "Assignment 12",
  "activity": {
    "id": "assign12",
    "title": "Assignment 12",
    "type": "Assignment",
    "abbreviation": "A12",
    "accepts_file_upload": true,
    "allowed_filetypes": ".pdf,.docx",
    "dropbox_multiple": true,
    "perfect_score": "10",
    "due_date": "2025-09-01T23:59:00Z"
  },
  "student_attachments": [
    {
      "name": "MyPaper.pdf",
      "path": "MyPaper.pdf",
      "type": "file",
      "source": "submission",
      "download_url": "https://api.agilixbuzz.com/cmd?cmd=getstudentsubmission&enrollmentid=4317&itemid=assign12&packagetype=file&filepath=MyPaper.pdf&inline=true&_token=..."
    }
  ],
  "q_and_a_pairs": [
    {
      "question": "Is this a multiple choice question?",
      "answer": "Yes",
      "interaction_type": "choice"
    },
    {
      "question": "Upload your work.",
      "answer": "https://api.agilixbuzz.com/cmd?cmd=getattemptfile&enrollmentid=4317&itemid=assign12&partid=5&filepath=paper.pdf&inline=true&_token=...",
      "interaction_type": "fileupload",
      "attachments": [
        {
          "name": "paper.pdf",
          "path": "paper.pdf",
          "type": "file",
          "source": "attempt-question",
          "questionid": "q-file",
          "partid": "5",
          "download_url": "https://api.agilixbuzz.com/cmd?cmd=getattemptfile&..."
        }
      ]
    }
  ]
}
```

## Buzz API commands used

| Need | Buzz command |
| --- | --- |
| Summarize a course content tree | `GetManifest` |
| Resolve one course content item | `GetItem` |
| List course content items | `GetItemList` |
| Resolve course metadata | `GetCourse2` |
| List courses in an explicit domain | `ListCourses` |
| Resolve privacy-redacted user metadata | `GetUser2` |
| Resolve one enrollment | `GetEnrollment3` |
| List a user's enrollments | `ListUserEnrollments` |
| List a course/entity roster | `ListEntityEnrollments` |
| Student answers + uploaded files | `GetStudentSubmission` (`packagetype=data`) |
| Resolve the item / assignment / custom activity title and type | `GetItem` (falls back to `GetItemList`) |
| Resolve question prompts and choice IDs into answer text | `ListQuestions` (falls back to obsolete `GetQuestionList`) |
| Download a submitted file (e.g. dropbox PDF) | `GetStudentSubmission` (`packagetype=file&filepath=…`) |
| Download a file uploaded to a `fileupload` question | `GetAttemptFile` |

Item types recognized via the `ItemType` enum include `Assignment`, `Assessment`, `Homework`, `Discussion`, `CustomActivity` (SCO), `Folder`, `AssetLink`, `Survey`, `Wiki`, `Blog`, `Journal`, and `Lesson`. Whether a student can attach files is derived from the item's `dropbox2` element (per Buzz's `DropboxElement` flags: File, GoogleFile, Image, Drawing, Audio, Video).

## Answer mapping by interaction type

| `interaction type` | Stored answer | Rendered answer |
| --- | --- | --- |
| `choice` | choice ID(s) | choice body text(s), comma-joined |
| `answer` | choice IDs (multi) | choice body texts, comma-joined |
| `order` | ordered choice IDs | choice body texts joined with `→` |
| `match` | `key=value` or positional choice IDs | `prompt → response`, comma-joined |
| `text` / `essay` | plain text | passthrough |
| `fileupload` | partid/path | authenticated download URL |
| `composite` / `custom` | passthrough | passthrough |

Question-level attachments are also exposed under the question's `attachments` array so a caller can grab the PDF directly even when the rendered answer is plain text or notes.
