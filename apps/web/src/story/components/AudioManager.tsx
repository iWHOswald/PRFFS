import { Volume2, VolumeX } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { Beat } from "../types";

export function useAudioManager(activeBeat?: Beat) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [muted, setMuted] = useState(true);

  useEffect(() => {
    if (!activeBeat || activeBeat.type !== "audio") return;
    if (activeBeat.action === "mute") {
      setMuted(true);
      return;
    }
    if (activeBeat.action === "unmute") {
      setMuted(false);
      return;
    }
    if (activeBeat.action === "stop") {
      audioRef.current?.pause();
      return;
    }
    if (activeBeat.action === "play" && activeBeat.src) {
      const audio = new Audio(activeBeat.src);
      audio.loop = Boolean(activeBeat.loop);
      audio.volume = activeBeat.volume ?? 0.5;
      audio.muted = muted;
      audioRef.current?.pause();
      audioRef.current = audio;
      audio.play().catch(() => undefined);
    }
  }, [activeBeat, muted]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.muted = muted;
  }, [muted]);

  return { muted, setMuted };
}

export function AudioToggle({ muted, setMuted }: { muted: boolean; setMuted: (muted: boolean) => void }) {
  return (
    <button type="button" onClick={() => setMuted(!muted)} aria-label={muted ? "Unmute story audio" : "Mute story audio"}>
      {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
    </button>
  );
}
