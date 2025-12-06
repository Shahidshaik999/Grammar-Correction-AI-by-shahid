import { motion } from "framer-motion";
import { Edit3 } from "lucide-react";
import { StatsBar } from "./StatsBar";

interface TextEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export function TextEditor({ value, onChange }: TextEditorProps) {
  return (
    <motion.div
      className="flex flex-col h-full"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-primary/15 flex items-center justify-center">
          <Edit3 className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="font-semibold text-foreground">Your Text</h2>
          <p className="text-xs text-muted-foreground">Type freely. We'll polish it automatically.</p>
        </div>
      </div>

      {/* Editor */}
      <div className="relative flex-1 glass-card rounded-xl overflow-hidden shadow-soft">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Start typing or paste your text here..."
          className="w-full h-full min-h-[320px] p-5 bg-transparent resize-none focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-inset rounded-xl font-mono text-[15px] leading-relaxed text-foreground placeholder:text-muted-foreground/50 transition-all scrollbar-custom"
        />
      </div>

      {/* Stats */}
      <div className="mt-3">
        <StatsBar text={value} />
      </div>
    </motion.div>
  );
}