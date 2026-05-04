import { Folder, ChevronDown, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useProjectFiles } from "@/hooks/use-projects";

interface Props {
  projectId: string;
  value?: string;
  onChange: (id?: string) => void;
}

export function DocumentScopeFilter({ projectId, value, onChange }: Props) {
  const { data: files = [] } = useProjectFiles(projectId);
  const active = files.find((f) => f.document_id === value);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" type="button">
          <Folder className="h-3.5 w-3.5" />
          <span className="max-w-[140px] truncate">
            {active ? active.filename_redacted : "All documents"}
          </span>
          <ChevronDown className="h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuItem onSelect={() => onChange(undefined)}>
          {!value && <Check className="h-3.5 w-3.5 text-primary" />}
          <span className={!value ? "font-medium" : ""}>All documents</span>
        </DropdownMenuItem>
        {files.map((f) => (
          <DropdownMenuItem
            key={f.document_id}
            onSelect={() => onChange(f.document_id)}
          >
            {value === f.document_id && (
              <Check className="h-3.5 w-3.5 text-primary" />
            )}
            <span
              className={`truncate ${value === f.document_id ? "font-medium" : ""}`}
            >
              {f.filename_redacted}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
