const SSN_PATTERN = /\b\d{3}-?\d{2}-?\d{4}\b/;
const DOB_PATTERN =
  /\b(0?[1-9]|1[0-2])[\/\-\.](0?[1-9]|[12]\d|3[01])[\/\-\.](19|20)\d{2}\b/;
const DISTRICT_ID_PATTERN = /\b\d{6,}\b/;
const TWO_CAPS_PATTERN = /\b[A-Z][a-z]+\s+[A-Z][a-z]+\b/;
const ISO_DATE_PATTERN = /\b(19|20)\d{2}-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01])\b/;

export type PiiCheckResult =
  | { ok: true }
  | { ok: false; reason: string };

export function detectPiiInLabel(label: string): PiiCheckResult {
  const trimmed = label.trim();
  if (trimmed.length === 0) {
    return { ok: false, reason: "Label is required." };
  }
  if (trimmed.length > 80) {
    return { ok: false, reason: "Label must be 80 characters or fewer." };
  }
  if (SSN_PATTERN.test(trimmed)) {
    return {
      ok: false,
      reason: "Looks like a Social Security number. Use a case code such as Case 2026-014.",
    };
  }
  if (DOB_PATTERN.test(trimmed) || ISO_DATE_PATTERN.test(trimmed)) {
    return {
      ok: false,
      reason:
        "Looks like a name and date of birth. Use a case code such as Case 2026-014. Names, birthdates, and 6+ digit IDs are blocked at the gateway.",
    };
  }
  if (DISTRICT_ID_PATTERN.test(trimmed)) {
    return {
      ok: false,
      reason: "Looks like a 6+ digit ID number. Use a case code such as Case 2026-014.",
    };
  }
  if (TWO_CAPS_PATTERN.test(trimmed)) {
    return {
      ok: false,
      reason:
        "Looks like a personal name. Use a case code such as Case 2026-014.",
    };
  }
  return { ok: true };
}

export function detectPiiSuggestion(label: string): "valid" | "empty" | "invalid" {
  if (label.trim().length === 0) return "empty";
  return detectPiiInLabel(label).ok ? "valid" : "invalid";
}
