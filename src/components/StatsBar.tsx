import { useMemo } from "react";
import { FileText, Hash } from "lucide-react";

interface StatsBarProps {
  text: string;
}

export function StatsBar({ text }: StatsBarProps) {
  const stats = useMemo(() => {
    const characters = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    return { characters, words };
  }, [text]);

  return (
    <div className="flex items-center gap-4 text-xs text-muted-foreground">
      <div className="flex items-center gap-1.5">
        <FileText className="w-3.5 h-3.5" />
        <span><span className="text-foreground font-medium">{stats.words}</span> words</span>
      </div>
      <div className="flex items-center gap-1.5">
        <Hash className="w-3.5 h-3.5" />
        <span><span className="text-foreground font-medium">{stats.characters}</span> chars</span>
      </div>
    </div>
  );
}