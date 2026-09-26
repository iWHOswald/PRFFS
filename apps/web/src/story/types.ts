import type { CSSProperties } from "react";

export type TextMode = "fade" | "typewriter" | "aether" | "hardCut" | "title" | "narration" | "dialogue";
export type CameraEasing = "linear" | "easeInOut" | "slowEase" | "cinematic" | "dramaticPush";
export type CameraPreset = "static" | "slowPush" | "slowPull" | "panLeft" | "panRight" | "panUp" | "panDown" | "drift" | "pushAndPan" | "pullAndReveal" | "subtleHandheld";
export type AtmosphereKind = "snow" | "rain" | "fog" | "dust" | "embers" | "none";

export type BloomFlare = {
  id: string;
  x: number;
  y: number;
  size: number;
  opacity?: number;
  color?: string;
  stretch?: number;
};

export type CameraKeyframe = {
  at: number;
  x?: number;
  y?: number;
  scale?: number;
  rotation?: number;
  originX?: number;
  originY?: number;
};

export type CameraConfig = {
  preset?: CameraPreset;
  target?: string;
  keyframes?: CameraKeyframe[];
  easing?: CameraEasing;
};

export type StoryLayer = {
  id: string;
  asset?: string;
  fit?: "cover" | "contain";
  color?: string;
  gradient?: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  scale?: number;
  opacity?: number;
  depth?: number;
  blur?: number;
  brightness?: number;
  contrast?: number;
  saturation?: number;
  blendMode?: CSSProperties["mixBlendMode"];
  visible?: boolean;
};

export type AtmosphereConfig = {
  kind: AtmosphereKind;
  density?: number;
  speed?: number;
  wind?: number;
  gustiness?: number;
  opacity?: number;
  direction?: number;
  sizeMin?: number;
  sizeMax?: number;
  motionBlur?: number;
  turbulence?: number;
  grain?: boolean;
};

export type TextConfig = {
  mode: TextMode;
  speaker?: string;
  text: string;
  placement?: "lower" | "center" | "upper" | "left" | "right";
  align?: "left" | "center" | "right";
  maxWidth?: number;
  staggerMs?: number;
  durationMs?: number;
  delayMs?: number;
};

export type Beat =
  | {
      id: string;
      type: "text";
      text: TextConfig;
    }
  | {
      id: string;
      type: "camera";
      action: CameraConfig;
    }
  | {
      id: string;
      type: "atmosphere";
      atmosphere: Partial<AtmosphereConfig>;
    }
  | {
      id: string;
      type: "lighting";
      tint?: string;
      intensity?: number;
    }
  | {
      id: string;
      type: "audio";
      action: "play" | "stop" | "mute" | "unmute";
      src?: string;
      volume?: number;
      loop?: boolean;
    };

export type Scene = {
  id: string;
  title: string;
  duration?: number;
  overscan?: number;
  camera?: CameraConfig;
  atmosphere?: AtmosphereConfig;
  bloom?: BloomFlare[];
  layers: StoryLayer[];
  beats: Beat[];
};

export type Chapter = {
  id: string;
  title: string;
  scenes: Scene[];
};

export type Story = {
  id: string;
  title: string;
  chapters: Chapter[];
};
