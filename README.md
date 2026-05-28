# Buzz Submission MCP

FastMCP server that turns Agilix Buzz student submissions into a human-readable JSON report — activity name resolved from the item ID, answers resolved from question/choice IDs, and authenticated download URLs for any submitted PDFs or other attachments.

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

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Tool

`get_complete_submission_report` accepts explicit IDs:

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
