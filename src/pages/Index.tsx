// src/pages/Index.tsx

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Layout } from "@/components/Layout";
import { ModeSelector } from "@/components/ModeSelector";
import { RealtimeToggle } from "@/components/RealtimeToggle";
import { TextEditor } from "@/components/TextEditor";
import { PolishedOutput } from "@/components/PolishedOutput";
import { PolishButton } from "@/components/PolishButton";
import {
  correctText,
  polishAI,
  rewriteTone,
  type CorrectionMode,
  type ToneMode,
} from "@/lib/polishApi";
import { useDebounce } from "@/hooks/useDebounce";

const toneOptions: { id: ToneMode; label: string; emoji: string }[] = [
  { id: "friendly", label: "Friendly", emoji: "😊" },
  { id: "professional", label: "Professional", emoji: "💼" },
  { id: "confident", label: "Confident", emoji: "🚀" },
  { id: "calm", label: "Calm Tone", emoji: "🧊" },
  { id: "caring", label: "Caring", emoji: "❤️" },
  { id: "persuasive", label: "Persuasive", emoji: "🤝" },
];

const Index = () => {
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [summary, setSummary] = useState("");
  const [mode, setMode] = useState<CorrectionMode>("grammar");
  const [realtimeEnabled, setRealtimeEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [aiMode, setAiMode] = useState(false); // grammar vs AI fluent
  const [activeTone, setActiveTone] = useState<ToneMode | null>(null);

  const debouncedText = useDebounce(inputText, 600);

  // Core function to process text (grammar / AI fluent)
  const processText = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) {
      setOutputText("");
      setSummary("");
      setActiveTone(null);
      return;
    }

    setIsLoading(true);
    try {
      let result;
      if (aiMode) {
        result = await polishAI(trimmed);
      } else {
        result = await correctText(trimmed, mode);
      }

      if (result) {
        setOutputText(result.correctedText);
        setSummary(result.changesSummary);
        setActiveTone(null); // reset tone when base output changes
      }
    } catch (err) {
      console.error("polish error", err);
      toast.error("Something went wrong while polishing. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Real-time processing with debounce
  useEffect(() => {
    if (!realtimeEnabled) return;

    const trimmed = debouncedText.trim();
    if (!trimmed) {
      setOutputText("");
      setSummary("");
      setActiveTone(null);
      return;
    }

    processText(trimmed);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedText, mode, aiMode, realtimeEnabled]);

  // Clear output when input is empty
  useEffect(() => {
    if (!inputText.trim()) {
      setOutputText("");
      setSummary("");
      setActiveTone(null);
    }
  }, [inputText]);

  const handlePolishNow = () => {
    processText(inputText);
  };

  const handleModeChange = (newMode: CorrectionMode) => {
    // when user switches grammar / professional / casual
    setAiMode(false); // go back to non-AI mode
    setMode(newMode);

    if (inputText.trim() && !realtimeEnabled) {
      processText(inputText);
    }
  };

  const handleAIButton = () => {
    setAiMode(true);
    if (inputText.trim()) {
      processText(inputText);
    }
  };

  // NEW: Tone transformer handler
  const handleToneClick = async (tone: ToneMode) => {
    const base = outputText.trim() || inputText.trim();
    if (!base) return;

    setIsLoading(true);
    setActiveTone(tone);

    try {
      const result = await rewriteTone(base, tone);
      if (result) {
        setOutputText(result.correctedText);
        setSummary(result.changesSummary);
      }
    } catch (err) {
      console.error("tone rewrite error", err);
      toast.error("Could not adjust tone. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {/* Hero section */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-3">
            Polish Your English <span className="gradient-text">Instantly</span>
          </h1>
          <p className="text-muted-foreground text-base sm:text-lg max-w-xl mx-auto">
            Type or paste your text and watch it transform into clear, professional English in real-time.
          </p>
        </motion.div>

        {/* Controls */}
        <motion.div
          className="flex flex-wrap items-center justify-center gap-4 mb-6"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <ModeSelector mode={mode} onModeChange={handleModeChange} />

          {/* AI Fluent button */}
          <button
            onClick={handleAIButton}
            className={`px-5 py-2 rounded-xl font-medium transition ${
              aiMode
                ? "bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white shadow"
                : "border border-purple-500 text-purple-500 hover:bg-purple-50"
            }`}
            disabled={!inputText.trim() || isLoading}
          >
            {isLoading && aiMode ? "Polishing with AI..." : "Make Fluent (AI)"}
          </button>

          <RealtimeToggle
            enabled={realtimeEnabled}
            onToggle={setRealtimeEnabled}
          />
        </motion.div>

        {/* Main editor card */}
        <motion.div
          className="glass-card rounded-2xl p-4 sm:p-6 lg:p-8"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
            {/* Input panel */}
            <TextEditor value={inputText} onChange={setInputText} />

            {/* Output + Tone panel */}
            <div className="flex flex-col gap-4">
              <PolishedOutput
                text={outputText}
                summary={summary}
                isLoading={isLoading}
              />

              {/* Tone Transformer (only show when we have output) */}
              {outputText.trim() && (
                <div className="rounded-xl bg-slate-900/60 border border-slate-700 px-3 py-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-slate-300">
                      Improve expression
                    </span>
                    <span className="text-[11px] text-slate-500">
                      Choose how you want it to sound
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {toneOptions.map((tone) => (
                      <button
                        key={tone.id}
                        onClick={() => handleToneClick(tone.id)}
                        disabled={isLoading}
                        className={`text-xs sm:text-[13px] px-3 py-1.5 rounded-full border transition flex items-center gap-1 ${
                          activeTone === tone.id
                            ? "bg-indigo-500/80 border-indigo-400 text-white"
                            : "border-slate-600 text-slate-200 hover:bg-slate-800"
                        }`}
                      >
                        <span>{tone.emoji}</span>
                        <span>{tone.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Polish button (shown when real-time is off) */}
          {!realtimeEnabled && (
            <motion.div
              className="mt-6 max-w-xs mx-auto"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <PolishButton
                onClick={handlePolishNow}
                isLoading={isLoading}
                disabled={!inputText.trim()}
              />
            </motion.div>
          )}
        </motion.div>
      </div>
    </Layout>
  );
};

export default Index;
