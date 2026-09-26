import type { CameraConfig, CameraKeyframe, CameraPreset } from "./types";

const presets: Record<CameraPreset, CameraKeyframe[]> = {
  static: [{ at: 0, x: 0, y: 0, scale: 1, rotation: 0 }],
  slowPush: [{ at: 0, scale: 1.03 }, { at: 24, scale: 1.13, y: -1 }],
  slowPull: [{ at: 0, scale: 1.14 }, { at: 24, scale: 1.03, y: 1 }],
  panLeft: [{ at: 0, x: 2, scale: 1.08 }, { at: 22, x: -4, scale: 1.1 }],
  panRight: [{ at: 0, x: -4, scale: 1.08 }, { at: 22, x: 2, scale: 1.1 }],
  panUp: [{ at: 0, y: 2, scale: 1.08 }, { at: 20, y: -4, scale: 1.1 }],
  panDown: [{ at: 0, y: -4, scale: 1.08 }, { at: 20, y: 2, scale: 1.1 }],
  drift: [{ at: 0, x: 0, y: 0, scale: 1.06 }, { at: 18, x: -2, y: 1, scale: 1.09 }],
  pushAndPan: [{ at: 0, x: 1, scale: 1.05 }, { at: 22, x: -5, y: -1, scale: 1.16, rotation: -0.12 }],
  pullAndReveal: [{ at: 0, x: -3, y: -1, scale: 1.18 }, { at: 24, x: 2, y: 1, scale: 1.06 }],
  subtleHandheld: [
    { at: 0, x: 0, y: 0, scale: 1.08, rotation: 0 },
    { at: 7, x: -0.4, y: 0.3, scale: 1.085, rotation: -0.05 },
    { at: 15, x: 0.5, y: -0.2, scale: 1.09, rotation: 0.04 },
    { at: 24, x: -0.2, y: 0.2, scale: 1.087, rotation: 0 }
  ]
};

export function cameraAnimation(config?: CameraConfig) {
  const keyframes = config?.keyframes?.length ? config.keyframes : presets[config?.preset ?? "slowPush"];
  const last = keyframes[keyframes.length - 1]?.at || 20;
  return {
    animate: {
      x: keyframes.map((frame) => `${frame.x ?? 0}%`),
      y: keyframes.map((frame) => `${frame.y ?? 0}%`),
      scale: keyframes.map((frame) => frame.scale ?? 1),
      rotate: keyframes.map((frame) => frame.rotation ?? 0),
      transformOrigin: keyframes.map((frame) => `${frame.originX ?? 50}% ${frame.originY ?? 50}%`)
    },
    transition: {
      duration: last,
      times: keyframes.map((frame) => Math.max(0, Math.min(1, frame.at / last))),
      ease: easing(config?.easing),
      repeat: Infinity,
      repeatType: "mirror" as const
    }
  };
}

export function easing(name = "cinematic") {
  if (name === "linear") return "linear";
  if (name === "easeInOut") return "easeInOut";
  if (name === "slowEase") return [0.45, 0, 0.2, 1];
  if (name === "dramaticPush") return [0.65, 0, 0.1, 1];
  return [0.37, 0, 0.16, 1];
}
