# SecurePsych — Audit Log Schema

**Purpose:** Documents the structure, storage, and retention policy of gateway access logs for FERPA compliance review by district auditors.

---

## Storage

- **Location:** `GATEWAY_LOG_DIR` env var → defaults to `/mnt/securepsych/data/gateway/logs` (LUKS-encrypted volume)
- **Format:** One JSON object per line (newline-delimited JSON), one file per day
- **Filename pattern:** `access_YYYY-MM-DD.log`
- **Retention:** `GATEWAY_LOG_RETENTION_DAYS` env var (default: 30 days). Files older than the retention window are deleted by the weekly systemd timer in `infra/log-retention.timer`. Confirm minimum with district auditors before reducing further.

---

## Log Record Schema

Each request to an authenticated endpoint produces one JSON log entry:

```json
{
  "ts":          "2026-05-01T14:23:07.412Z",
  "user_id":     "psychologist-username",
  "role":        "psychologist",
  "method":      "POST",
  "path":        "/api/rag/query",
  "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
  "status":      200,
  "duration_ms": 1840
}
```

| Field         | Type   | Description                                              |
| ------------- | ------ | -------------------------------------------------------- |
| `ts`          | string | UTC ISO-8601 timestamp of request completion             |
| `user_id`     | string | Authenticated username from JWT (`sub` claim)            |
| `role`        | string | User role from JWT (`role` claim)                        |
| `method`      | string | HTTP method                                              |
| `path`        | string | Request path (never includes query strings with PII)     |
| `document_id` | string | Extracted from URL path if present; otherwise omitted    |
| `status`      | int    | HTTP response status code                                |
| `duration_ms` | int    | End-to-end request duration in milliseconds              |

---

## What Is NOT Logged (FERPA boundary)

- Query text / student questions
- Document content or summaries
- Raw student identifiers (student IDs, names, DOBs)
- JWT token values

The logging policy mirrors the LangSmith metadata-only constraint: only who accessed what endpoint at what time, never the content of the access.

---

## Access Policy

- Log files are owned by the process user running the gateway service (e.g. `securepsych`)
- Read access restricted to `securepsych` user and `secadmin` group (district IT)
- Log directory permissions: `750` (owner rwx, group rx, others none)
- Auditors access logs via a read-only `secadmin` shell session on the server — logs are never transmitted off-site

---

## Implementation Reference

- Logging middleware: `backend/gateway/middleware/logging.py`
- Log directory config: `backend/gateway/config.py` → `settings.storage.log_dir`
- Retention enforcement: automated via `infra/log-retention.service` + `infra/log-retention.timer` (weekly systemd timer)
