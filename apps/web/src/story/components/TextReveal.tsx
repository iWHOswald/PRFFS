import { motion } from "framer-motion";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import type { TextConfig } from "../types";

type Props = {
  text: TextConfig;
  forceComplete: boolean;
  onComplete: () => void;
};

export function TextReveal({ text, forceComplete, onComplete }: Props) {
  const [complete, setComplete] = useState(false);
  const chars = useMemo(() => Array.from(text.text), [text.text]);
  const stagger = text.staggerMs ?? (text.mode === "aether" ? 32 : 18);
  const duration = text.durationMs ?? (text.mode === "aether" ? 760 : 420);
  const delay = text.delayMs ?? 0;

  useEffect(() => {
    setComplete(false);
    const total = text.mode === "hardCut" ? 0 : delay + chars.length * stagger + duration;
    const handle = window.setTimeout(() => {
      setComplete(true);
      onComplete();
    }, total);
    return () => window.clearTimeout(handle);
  }, [chars.length, delay, duration, onComplete, stagger, text.mode, text.text]);

  useEffect(() => {
    if (forceComplete && !complete) {
      setComplete(true);
      onComplete();
    }
  }, [complete, forceComplete, onComplete]);

  if (text.mode === "hardCut" || forceComplete || complete) {
    return <TextFrame text={text}>{text.text}</TextFrame>;
  }

  if (text.mode === "fade" || text.mode === "narration" || text.mode === "dialogue") {
    return (
      <TextFrame text={text}>
        <motion.span initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: duration / 1000, delay: delay / 1000 }}>
          {text.text}
        </motion.span>
      </TextFrame>
    );
  }

  return (
    <TextFrame text={text}>
      {chars.map((char, index) => (
        <motion.span
          aria-hidden="true"
          className="story-char"
          initial={{
            opacity: 0,
            y: text.mode === "aether" ? 7 : 0,
            filter: text.mode === "aether" ? "blur(8px)" : "blur(0px)"
          }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ duration: duration / 1000, delay: (delay + index * stagger) / 1000, ease: [0.22, 1, 0.36, 1] }}
          key={`${char}-${index}`}
        >
          {char === " " ? "\u00a0" : char}
        </motion.span>
      ))}
      <span className="sr-only">{text.text}</span>
    </TextFrame>
  );
}

function TextFrame({ text, children }: { text: TextConfig; children: ReactNode }) {
  return (
    <div
      className={`story-text story-text-${text.placement ?? "lower"} story-align-${text.align ?? "left"} story-text-${text.mode}`}
      style={{ maxWidth: text.maxWidth ? `${text.maxWidth}px` : undefined }}
    >
      {text.speaker ? <span className="story-speaker">{text.speaker}</span> : null}
      <p>{children}</p>
    </div>
  );
}
