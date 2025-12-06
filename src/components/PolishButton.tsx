import { motion } from "framer-motion";
import { Wand2, Loader2 } from "lucide-react";

interface PolishButtonProps {
  onClick: () => void;
  isLoading: boolean;
  disabled: boolean;
}

export function PolishButton({ onClick, isLoading, disabled }: PolishButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled || isLoading}
      className="flex items-center justify-center gap-2 w-full sm:w-auto px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:brightness-110"
      whileHover={{ scale: !disabled && !isLoading ? 1.02 : 1 }}
      whileTap={{ scale: !disabled && !isLoading ? 0.98 : 1 }}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Polishing...</span>
        </>
      ) : (
        <>
          <Wand2 className="w-5 h-5" />
          <span>Polish Now</span>
        </>
      )}
    </motion.button>
  );
}