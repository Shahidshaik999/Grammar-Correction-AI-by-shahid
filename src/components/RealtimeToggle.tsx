import { motion } from "framer-motion";
import { Switch } from "@/components/ui/switch";
import { Zap } from "lucide-react";

interface RealtimeToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export function RealtimeToggle({ enabled, onToggle }: RealtimeToggleProps) {
  return (
    <motion.div 
      className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-secondary/60"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2 }}
    >
      <Switch 
        checked={enabled} 
        onCheckedChange={onToggle}
        className="data-[state=checked]:bg-primary"
      />
      <div className="flex items-center gap-2">
        <Zap className={`w-4 h-4 transition-colors ${enabled ? "text-primary" : "text-muted-foreground"}`} />
        <span className={`text-sm font-medium transition-colors ${enabled ? "text-foreground" : "text-muted-foreground"}`}>
          Real-time
        </span>
      </div>
    </motion.div>
  );
}