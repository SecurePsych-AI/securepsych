import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CitationFootnotes } from "@/components/chat/CitationFootnotes";
import type { Citation } from "@/types/api";

const citations: Citation[] = [
  {
    source: "eval_2024_REDACTED.pdf",
    page: 12,
    parent_id: "12_2",
    document_id: "doc-1",
  },
  {
    source: "eval_2024_REDACTED.pdf",
    page: 13,
    parent_id: "13_0",
    document_id: "doc-1",
  },
];

describe("<CitationFootnotes />", () => {
  it("renders nothing when there are no citations", () => {
    const { container } = render(<CitationFootnotes citations={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders one footnote per citation with numbered chips", () => {
    render(<CitationFootnotes citations={citations} />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getAllByText(/eval_2024_REDACTED\.pdf/i)).toHaveLength(2);
    expect(screen.getByText(/page 12/i)).toBeInTheDocument();
    expect(screen.getByText(/page 13/i)).toBeInTheDocument();
  });
});
