import type {
  Citation,
  JargonLevel,
  Project,
  RagPreviewResponse,
  RagUploadResponse,
  SummaryRun,
  Thread,
  UploadedFile,
  UUID,
} from "@/types/api";

export const PROJECT_A: Project = {
  id: "a1b2c3d4-0001-0001-0001-000000000001",
  display_label: "Case 2026-014",
  created_at: "2026-04-30T14:22:07.123456+00:00",
};

export const PROJECT_B: Project = {
  id: "b2c3d4e5-0002-0002-0002-000000000002",
  display_label: "Case 2026-008",
  created_at: "2026-04-21T09:10:31.000000+00:00",
};

export const DOCUMENT_ID: UUID = "f7e6d5c4-b3a2-9180-7654-3210fedcba98";

export const FILE_A: UploadedFile = {
  id: "c3d4e5f6-0003-0003-0003-000000000003",
  document_id: DOCUMENT_ID,
  filename_redacted: "eval_2024_REDACTED.pdf",
  strategy: "standard",
  chunks_added: 187,
  uploaded_at: "2026-04-30T14:30:55.000000+00:00",
};

export const THREAD_A: Thread = {
  id: "cc1d2e3f-4a5b-6c7d-8e9f-a0b1c2d3e4f5",
  title: "Cognitive scores · WISC-V",
  created_at: "2026-04-30T14:45:00.000000+00:00",
};

export const SAMPLE_CITATIONS: Citation[] = [
  {
    source: "eval_2024_REDACTED.pdf",
    page: 12,
    parent_id: "12_2",
    document_id: DOCUMENT_ID,
  },
  {
    source: "eval_2024_REDACTED.pdf",
    page: 13,
    parent_id: "13_0",
    document_id: DOCUMENT_ID,
  },
  {
    source: "eval_2024_REDACTED.pdf",
    page: 18,
    parent_id: "18_1",
    document_id: DOCUMENT_ID,
  },
];

export const SAMPLE_RAG_ANSWER =
  "The Wechsler Intelligence Scale for Children (WISC-V) was administered. The student obtained a Full Scale IQ (FSIQ) composite score of 88, placing performance in the Low Average range (25th percentile). The Verbal Comprehension Index was 92, the Fluid Reasoning Index was 85, and the Processing Speed Index was 79.";

export const SAMPLE_PREVIEW: RagPreviewResponse = {
  preview_token: "9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  sample_text:
    "This psychoeducational evaluation was conducted for STUDENT_NAME_1, a 10-year-old in 4th grade. Date of birth: DATE_OF_BIRTH_1. The evaluation was completed on EVAL_DATE_1 by EXAMINER_NAME_1, M.A., NCSP. Referral source: PARENT_NAME_1, parent.",
  entity_map: {
    STUDENT_NAME_1: "Marcus Johnson",
    DATE_OF_BIRTH_1: "01/15/2012",
    EVAL_DATE_1: "03/15/2024",
    EXAMINER_NAME_1: "Dr. Sarah Lee",
    PARENT_NAME_1: "Angela Johnson",
  },
  page_count: 24,
  filename: "eval_2024.pdf",
};

export const SAMPLE_UPLOAD: RagUploadResponse = {
  status: "ok",
  document_id: DOCUMENT_ID,
  source: "eval_2024_REDACTED.pdf",
  strategy: "standard",
  chunks_added: 187,
  avg_chunk_tokens: 512,
};

export const SAMPLE_SUMMARY: SummaryRun = {
  id: "f3a4b5c6-d7e8-9f0a-1b2c-d3e4f5a6b7c8",
  document_id: DOCUMENT_ID,
  filename_redacted: "eval_2024_REDACTED.pdf",
  page_count: 24,
  created_at: "2026-04-30T15:02:11.000000+00:00",
  summary: `Psychoeducational Evaluation Summary

Student Information: 10-year-old, 4th grade. Evaluation completed March 15, 2024 by a licensed school psychologist.

Referral Concerns: Difficulties with reading fluency, comprehension, written expression; possible ADHD concerns.

Cognitive Assessment (WISC-V):
- Full Scale IQ: 88 (Low Average, 25th percentile)
- Verbal Comprehension Index: 92 (Average)
- Fluid Reasoning Index: 85 (Low Average)
- Processing Speed Index: 79 (Below Average, 8th percentile)

Academic Achievement (WIAT-4):
- Word Reading: 74 (4th percentile) — significantly below grade level
- Reading Comprehension: 78 (7th percentile)
- Spelling: 76 (5th percentile)
- Math Problem Solving: 91 (27th percentile)

Diagnoses Indicated: Specific Learning Disability in Reading (Dyslexia). ADHD Inattentive Type noted as differential requiring further evaluation.

Recommendations: Orton-Gillingham reading instruction, extended time on assessments, preferential seating, reading specialist pull-out 3x/week.`,
};

export const JARGON_BY_LEVEL: Record<JargonLevel, { simplified_text: string; flesch_kincaid_grade: number }> = {
  1: {
    simplified_text:
      "The student presents with deficits in phonological processing (CTOPP-2: PMC SS=74, 4th %ile; PAC SS=71, 3rd %ile). Findings meet DSM-5 criteria for SLD with Impairment in Reading (315.00), consistent with developmental dyslexia.",
    flesch_kincaid_grade: 14.2,
  },
  2: {
    simplified_text:
      "Testing indicates the student has a learning disability in reading. Phonological processing scores fell at the 3rd–4th percentile. Recommend structured literacy intervention (e.g., Orton-Gillingham) with progress monitoring every 2 weeks.",
    flesch_kincaid_grade: 11.4,
  },
  3: {
    simplified_text:
      "The testing showed that your child has difficulty with the sound-based building blocks of reading — things like remembering the sounds in words and recognizing how words break into smaller sound parts. These scores were in the low range compared to other children the same age, which is why the evaluation found that your child has a reading learning disability (sometimes called dyslexia). This is something we can directly support with the right teaching approach.",
    flesch_kincaid_grade: 7.1,
  },
  4: {
    simplified_text:
      "The tests showed it's harder for you to break words into their sound parts. That's a common kind of reading challenge — it has a name (dyslexia), and your school can give you a reading method made for exactly this.",
    flesch_kincaid_grade: 5.6,
  },
  5: {
    simplified_text:
      "Some people find it harder to hear all the little sounds in words. Like, the word 'cat' has three sounds: k-a-t. Your brain sometimes has a tough time with that, and that's okay! It just means you learn to read in a slightly different way, and teachers can help you with special reading games.",
    flesch_kincaid_grade: 3.8,
  },
};

export const SAMPLE_JARGON_INPUT_PREVIEW =
  "The examinee demonstrated significant deficits in phonological processing as measured by the CTOPP-2, with a Phonological Memory Composite of 74 (4th percentil";
