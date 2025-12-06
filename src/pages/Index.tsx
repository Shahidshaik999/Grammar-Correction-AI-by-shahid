import { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";

import { Layout } from "@/components/Layout";
import { TextEditor } from "@/components/TextEditor";
import { PolishedOutput } from "@/components/PolishedOutput";
import { PolishButton } from "@/components/PolishButton";

import {
  polishText,
  polishWithAI,
  type Mode,
  type ToneMode,
  type StyleProfile,
} from "@/lib/polishApi";

const grammarModes: { id: Mode; label: string }[] = [
  { id: "grammar", label: "Fix Grammar" },
  { id: "casual", label: "Make Casual" },
  { id: "professional", label: "Make Professional" },
];

const toneOptions: { id: ToneMode; label: string; emoji: string }[] = [
  { id: "friendly", emoji: "😊", label: "Friendly" },
  { id: "professional", emoji: "💼", label: "Professional" },
  { id: "confident", emoji: "💪", label: "Confident" },
  { id: "caring", emoji: "❤️", label: "Caring" },
  { id: "persuasive", emoji: "🤝", label: "Persuasive" },
  { id: "calm", emoji: "🧊", label: "Calm Tone" },
];

const styleOptions: { id: StyleProfile; label: string }[] = [
  { id: "neutral", label: "Default" },
  { id: "student", label: "Student / Simple" },
  { id: "corporate", label: "Corporate / Job" },
  { id: "ielts", label: "IELTS / Academic" },
  { id: "romantic", label: "Soft / Caring" },
];

const Index = () => {
  const [mode, setMode] = useState<Mode>("grammar");
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [summary, setSummary] = useState("");

  const [isLoading, setIsLoading] = useState(false);

  // Smart rewrite controls
  const [activeTone, setActiveTone] = useState<ToneMode>("friendly");
  const [styleProfile, setStyleProfile] = useState<StyleProfile>("neutral");

  const [realtime, setRealtime] = useState<boolean>(false);

  const hasText = inputText.trim().length > 0;

  // ------------------------
  // Basic grammar polish
  // ------------------------
  const handleGrammarPolish = async (nextMode: Mode) => {
    setMode(nextMode);
    if (!hasText) return;

    try {
      setIsLoading(true);
      const res = await polishText(inputText, nextMode);
      if (!res) {
        toast.error("Backend did not respond. Please check server.");
        return;
      }
      setOutputText(res.correctedText);
      setSummary(res.changesSummary);
    } catch (err) {
      console.error(err);
      toast.error("Something went wrong while polishing.");
    } finally {
      setIsLoading(false);
    }
  };

  // ------------------------
  // Smart Rewrite v3 (AI)
  // ------------------------
  const runSmartRewrite = async (
    tone: ToneMode = activeTone,
    style: StyleProfile = styleProfile
  ) => {
    if (!hasText) return;

    try {
      setIsLoading(true);
      const res = await polishWithAI(inputText, tone, style);
      if (!res) {
        toast.error("AI rewrite failed. Please check backend.");
        return;
      }
      setOutputText(res.correctedText);
      setSummary(res.changesSummary);
    } catch (err) {
      console.error(err);
      toast.error("Something went wrong with AI rewrite.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleMakeFluentClick = async () => {
    await runSmartRewrite();
  };

  const handleToneClick = async (tone: ToneMode) => {
    setActiveTone(tone);
    if (!hasText) return;
    await runSmartRewrite(tone, styleProfile);
  };

  const handleStyleClick = async (style: StyleProfile) => {
    setStyleProfile(style);
    if (!hasText) return;
    await runSmartRewrite(activeTone, style);
  };

  // Optional realtime toggle – when ON, grammar mode auto-runs
  const handleRealtimeToggle = async () => {
    const next = !realtime;
    setRealtime(next);
    if (next && hasText) {
      await handleGrammarPolish(mode);
    }
  };

  const handleInputChange = (value: string) => {
    setInputText(value);
    if (!value.trim()) {
      setOutputText("");
      setSummary("");
      return;
    }

    if (realtime) {
      // Simple realtime = just grammar mode
      handleGrammarPolish(mode);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-10">
        {/* Hero */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-3">
            Polish Your English <span className="gradient-text">Instantly</span>
          </h1>
          <p className="text-muted-foreground text-base sm:text-lg max-w-2xl mx-auto">
            Type or paste your message and transform it into clear, fluent
            English – with the exact tone and style you want.
          </p>
        </motion.div>

        {/* Top controls */}
        <motion.div
          className="flex flex-wrap items-center justify-center gap-3 mb-6"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {grammarModes.map((m) => (
            <button
              key={m.id}
              onClick={() => handleGrammarPolish(m.id)}
              className={`px-4 py-2 rounded-full text-sm font-medium border transition ${
                mode === m.id
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {m.label}
            </button>
          ))}

          <button
            onClick={handleMakeFluentClick}
            className="px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-fuchsia-500 to-blue-500 text-white shadow hover:opacity-90 transition"
          >
            Make Fluent (AI)
          </button>

          {/* Realtime toggle */}
          <button
            onClick={handleRealtimeToggle}
            className={`ml-2 text-xs px-3 py-1 rounded-full border transition ${
              realtime
                ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                : "bg-muted border-muted-foreground/30 text-muted-foreground"
            }`}
          >
            ⚡ Real-time {realtime ? "On" : "Off"}
          </button>
        </motion.div>

        {/* Main editor card */}
        <motion.div
          className="glass-card rounded-2xl p-4 sm:p-6 lg:p-8"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
            <TextEditor value={inputText} onChange={handleInputChange} />

            <PolishedOutput
              text={outputText}
              summary={summary}
              isLoading={isLoading}
            />
          </div>

          {/* AI controls under output */}
          <div className="mt-6 border-t border-border/40 pt-4 space-y-3">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
                  Improve expression
                </p>
                <div className="flex flex-wrap gap-2">
                  {toneOptions.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleToneClick(t.id)}
                      className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs border transition ${
                        activeTone === t.id
                          ? "bg-primary/90 text-primary-foreground border-primary"
                          : "bg-muted text-muted-foreground border-border hover:bg-muted/80"
                      }`}
                    >
                      <span>{t.emoji}</span>
                      <span>{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
                  Writing style
                </p>
                <div className="flex flex-wrap gap-2">
                  {styleOptions.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => handleStyleClick(s.id)}
                      className={`px-3 py-1.5 rounded-full text-xs border transition ${
                        styleProfile === s.id
                          ? "bg-secondary text-secondary-foreground border-secondary"
                          : "bg-muted text-muted-foreground border-border hover:bg-muted/80"
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Manual AI button for non-realtime users on mobile */}
            <div className="mt-2 max-w-xs">
              <PolishButton
                onClick={handleMakeFluentClick}
                isLoading={isLoading}
                disabled={!hasText}
              />
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
};

export default Index;
