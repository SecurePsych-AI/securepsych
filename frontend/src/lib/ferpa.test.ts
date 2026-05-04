import { describe, it, expect } from "vitest";
import { detectPiiInLabel } from "@/lib/ferpa";

describe("detectPiiInLabel", () => {
  it("accepts a valid case code", () => {
    expect(detectPiiInLabel("Case 2026-014")).toEqual({ ok: true });
  });

  it("rejects empty labels", () => {
    expect(detectPiiInLabel("")).toMatchObject({ ok: false });
    expect(detectPiiInLabel("   ")).toMatchObject({ ok: false });
  });

  it("rejects two consecutive capitalized words (name heuristic)", () => {
    const r = detectPiiInLabel("John Doe");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason.toLowerCase()).toContain("name");
  });

  it("rejects mm/dd/yyyy dates", () => {
    const r = detectPiiInLabel("Case 01/15/2012");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason.toLowerCase()).toMatch(/birthdate|date of birth/);
  });

  it("rejects 6+ digit district IDs", () => {
    const r = detectPiiInLabel("Case 123456");
    expect(r.ok).toBe(false);
  });

  it("rejects SSN-shaped strings", () => {
    expect(detectPiiInLabel("123-45-6789").ok).toBe(false);
  });

  it("rejects labels longer than 80 chars", () => {
    const long = "Case " + "x".repeat(80);
    expect(detectPiiInLabel(long).ok).toBe(false);
  });

  it("reproduces the canonical demo block: 'John Doe DOB 01/15/2012'", () => {
    const r = detectPiiInLabel("John Doe DOB 01/15/2012");
    expect(r.ok).toBe(false);
  });
});
