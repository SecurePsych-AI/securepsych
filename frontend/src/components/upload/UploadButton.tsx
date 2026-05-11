import { useRef } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
  variant?: "ghost" | "outline" | "default";
  label?: string;
}

export function UploadButton({
  onFile,
  disabled,
  variant = "ghost",
  label = "Attach PDF",
}: Props) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={ref}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
      <Button
        type="button"
        variant={variant}
        size="sm"
        onClick={() => ref.current?.click()}
        disabled={disabled}
      >
        <Upload className="h-3.5 w-3.5" />
        {label}
      </Button>
    </>
  );
}
