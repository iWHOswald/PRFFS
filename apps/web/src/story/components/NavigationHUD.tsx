import { ChevronLeft, ChevronRight } from "lucide-react";
import type { RefObject } from "react";
import { AudioToggle } from "./AudioManager";
import { FullscreenControl } from "./FullscreenControl";

type Props = {
  sceneIndex: number;
  sceneCount: number;
  beatIndex: number;
  beatCount: number;
  muted: boolean;
  setMuted: (muted: boolean) => void;
  stageRef: RefObject<HTMLElement>;
  onPrevious: () => void;
  onNext: () => void;
};

export function NavigationHUD({ sceneIndex, sceneCount, beatIndex, beatCount, muted, setMuted, stageRef, onPrevious, onNext }: Props) {
  const progress = ((sceneIndex + Math.min(1, (beatIndex + 1) / Math.max(1, beatCount))) / Math.max(1, sceneCount)) * 100;
  return (
    <nav className="story-hud" aria-label="Story controls">
      <button type="button" onClick={onPrevious} aria-label="Previous beat or scene">
        <ChevronLeft size={26} />
      </button>
      <div className="story-progress" aria-label={`Scene ${sceneIndex + 1} of ${sceneCount}, beat ${beatIndex + 1} of ${beatCount}`}>
        <span style={{ width: `${progress}%` }} />
      </div>
      <button type="button" onClick={onNext} aria-label="Next beat or scene">
        <ChevronRight size={26} />
      </button>
      <AudioToggle muted={muted} setMuted={setMuted} />
      <FullscreenControl targetRef={stageRef} />
    </nav>
  );
}
