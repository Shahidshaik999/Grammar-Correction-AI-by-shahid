import { motion } from "framer-motion";
import { Check, Sparkles, MessageSquare, Briefcase } from "lucide-react";
import type { CorrectionMode } from "@/lib/polishApi";

interface ModeSelectorProps {
  mode: CorrectionMode;
  onModeChange: (mode: CorrectionMode) => void;
}

const modes = [
  {
    id: "grammar" as CorrectionMode,
    label: "Fix Grammar",
    icon: Check,
  },
  {
    id: "casual" as CorrectionMode,
    label: "Make Casual",
    icon: MessageSquare,
  },
  {
    id: "professional" as CorrectionMode,
    label: "Make Professional",
    icon: Briefcase,
  },
  {
    id: "fluent" as CorrectionMode,
    label: "Make Fluent",
    icon: Sparkles,
  },
];

export function ModeSelector({ mode, onModeChange }: ModeSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {modes.map((m) => {
        const isActive = mode === m.id;
        const Icon = m.icon;

        return (
          <motion.button
            key={m.id}
            onClick={() => onModeChange(m.id)}
            className={`
              relative flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
              transition-all duration-200
              ${isActive 
                ? "bg-primary text-primary-foreground" 
                : "bg-secondary/60 text-muted-foreground hover:text-foreground hover:bg-secondary"
              }
            `}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Icon className="w-4 h-4" />
            <span>{m.label}</span>
          </motion.button>
        );
      })}
    </div>
  );
}