import { MessageSquare, FileText, Languages, BarChart3, ListTodo } from "lucide-react";

import { FeatureCard } from "@/components/dashboard/FeatureCard";
import { useFeatureFlags } from "@/hooks/use-feature-flags";

interface Props {
  projectId?: string | null;
}

export function FeatureCardGrid({ projectId }: Props) {
  const { data: flags } = useFeatureFlags();
  const base = projectId ? `/p/${projectId}` : null;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <FeatureCard
        icon={MessageSquare}
        title="Q&A Assistant"
        description="Ask questions across uploaded evaluations. Every answer cites a source."
        href={base ? `${base}/qa` : "/"}
        disabled={!base || !flags?.rag_enabled}
      />
      <FeatureCard
        icon={FileText}
        title="Document Summarizer"
        description="Generate a structured psychoeducational summary from a long PDF."
        href={base ? `${base}/summarize` : "/"}
        disabled={!base || !flags?.summarizer_enabled}
      />
      <FeatureCard
        icon={Languages}
        title="Jargon Simplifier"
        description="Rewrite clinical text at one of five reading levels — psychologist to elementary."
        href={base ? `${base}/jargon` : "/"}
        disabled={!base || !flags?.jargon_enabled}
      />
      <FeatureCard
        icon={BarChart3}
        title="Data Visualization"
        description="Score charts and trend lines across a student's evaluations."
        href="#"
        disabled
        comingSoon
      />
      <FeatureCard
        icon={ListTodo}
        title="Task Manager"
        description="Track IEP deadlines, parent meetings, and report drafts."
        href="#"
        disabled
        comingSoon
      />
    </div>
  );
}
