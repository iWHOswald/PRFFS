import { Maximize, Minimize } from "lucide-react";
import { useEffect, useState, type RefObject } from "react";

export function FullscreenControl({ targetRef }: { targetRef: RefObject<HTMLElement> }) {
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    const listener = () => setFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", listener);
    return () => document.removeEventListener("fullscreenchange", listener);
  }, []);

  function toggle() {
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => undefined);
      return;
    }
    targetRef.current?.requestFullscreen?.().catch(() => undefined);
  }

  return (
    <button type="button" onClick={toggle} aria-label={fullscreen ? "Exit fullscreen" : "Enter fullscreen"}>
      {fullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
    </button>
  );
}
