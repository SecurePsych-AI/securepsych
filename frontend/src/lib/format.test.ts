import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { relativeTime } from "@/lib/format";

describe("relativeTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-05-03T12:00:00Z"));
  });
  afterEach(() => vi.useRealTimers());

  it("returns 'just now' for <60s ago", () => {
    expect(relativeTime("2026-05-03T11:59:30Z")).toBe("just now");
  });

  it("returns minutes for 1–60 min ago", () => {
    expect(relativeTime("2026-05-03T11:55:00Z")).toBe("5 min ago");
  });

  it("returns hours for 1–24 hr ago", () => {
    expect(relativeTime("2026-05-03T09:00:00Z")).toBe("3 hr ago");
  });

  it("returns days for 1–7 d ago", () => {
    expect(relativeTime("2026-05-01T12:00:00Z")).toBe("2 d ago");
  });

  it("falls back to a locale date string for >7 d ago", () => {
    const out = relativeTime("2026-04-01T12:00:00Z");
    expect(out).not.toMatch(/ago/);
  });
});
