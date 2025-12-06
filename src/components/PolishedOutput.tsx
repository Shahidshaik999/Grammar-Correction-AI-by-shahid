import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Copy, Check, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface PolishedOutputProps {
  text: string;
  summary: string;
  isLoading: boolean;
}

export function PolishedOutput({ text, summary, isLoading }: PolishedOutputProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!text) return;
    
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success("Copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy text");
    }
  };

  return (
    <motion.div
      className="flex flex-col h-full"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent/15 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h2 className="font-semibold text-foreground">Polished Output</h2>
            <p className="text-xs text-muted-foreground">Your improved text appears here.</p>
          </div>
        </div>

        {/* Copy Button */}
        <motion.button
          onClick={handleCopy}
          disabled={!text || isLoading}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:brightness-110"
          whileHover={{ scale: text && !isLoading ? 1.02 : 1 }}
          whileTap={{ scale: text && !isLoading ? 0.98 : 1 }}
        >
          <AnimatePresence mode="wait">
            {copied ? (
              <motion.div
                key="check"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
              >
                <Check className="w-4 h-4" />
              </motion.div>
            ) : (
              <motion.div
                key="copy"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
              >
                <Copy className="w-4 h-4" />
              </motion.div>
            )}
          </AnimatePresence>
          <span>{copied ? "Copied!" : "Copy"}</span>
        </motion.button>
      </div>

      {/* Output Card */}
      <div className="relative flex-1 glass-card rounded-xl shadow-soft min-h-[320px] overflow-hidden">
        <div className="absolute inset-0 p-5 overflow-auto scrollbar-custom">
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center h-full"
              >
                <div className="flex items-center gap-3 text-muted-foreground">
                  <Loader2 className="w-5 h-5 animate-spin text-primary" />
                  <span className="text-sm">Polishing your text...</span>
                </div>
              </motion.div>
            ) : text ? (
              <motion.p
                key="text"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
                className="font-mono text-[15px] leading-relaxed text-foreground whitespace-pre-wrap"
              >
                {text}
              </motion.p>
            ) : (
              <motion.p
                key="placeholder"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-muted-foreground/50 italic text-sm"
              >
                Your polished text will appear here...
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Changes Summary */}
      <AnimatePresence>
        {summary && !isLoading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 overflow-hidden"
          >
            <div className="p-3 rounded-lg bg-accent/10 border border-accent/20">
              <p className="text-xs text-accent font-medium">
                <span className="opacity-70">Changes:</span> {summary}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}