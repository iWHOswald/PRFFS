import type { Story } from "./types";

export const demoStory: Story = {
  id: "neutral-engine-demo",
  title: "Cinematic Story System Demo",
  chapters: [
    {
      id: "chapter-00-engine-lab",
      title: "Engine Lab",
      scenes: [
        {
          id: "001-atmosphere-test",
          title: "Atmosphere Test",
          overscan: 16,
          camera: { preset: "pushAndPan", easing: "cinematic" },
          atmosphere: { kind: "snow", density: 90, speed: 0.42, wind: -0.14, gustiness: 0.3, opacity: 0.84, grain: true },
          layers: [
            { id: "sky", gradient: "linear-gradient(180deg, #081015 0%, #182622 52%, #3d3c34 100%)", width: 120, height: 120, x: -10, y: -10, depth: 0.05 },
            { id: "distant-light", gradient: "radial-gradient(circle at 50% 50%, rgba(242,193,78,0.4), rgba(242,193,78,0.05) 36%, transparent 62%)", width: 44, height: 44, x: 52, y: 32, opacity: 0.75, depth: 0.18, blur: 1 },
            { id: "ridge", gradient: "linear-gradient(150deg, transparent 0 45%, rgba(11,17,17,0.88) 46% 100%)", width: 130, height: 82, x: -18, y: 38, depth: 0.34 },
            { id: "foreground", gradient: "linear-gradient(12deg, rgba(3,7,8,0.98) 0 34%, transparent 35% 100%)", width: 130, height: 65, x: -12, y: 50, depth: 0.9 }
          ],
          beats: [
            { id: "beat-title", type: "text", text: { mode: "title", text: "ENGINE DEMO", placement: "center", align: "center", staggerMs: 32, durationMs: 850, maxWidth: 680 } },
            { id: "beat-narration", type: "text", text: { mode: "aether", text: "A neutral scene tests camera movement, layered depth, atmosphere, and paced narrative beats.", placement: "lower", staggerMs: 24, durationMs: 720, maxWidth: 760 } },
            { id: "beat-camera", type: "camera", action: { keyframes: [{ at: 0, x: -1, y: 0, scale: 1.11 }, { at: 14, x: -6, y: -2, scale: 1.18, rotation: -0.12 }], easing: "dramaticPush" } },
            { id: "beat-dialogue", type: "text", text: { mode: "dialogue", speaker: "SYSTEM", text: "Future scenes can replace this with approved art and canonical material.", placement: "lower", staggerMs: 18, durationMs: 620, maxWidth: 720 } }
          ]
        },
        {
          id: "002-light-and-rain-test",
          title: "Light And Rain Test",
          overscan: 12,
          camera: { preset: "slowPull", easing: "slowEase" },
          atmosphere: { kind: "rain", density: 130, speed: 1.1, wind: -0.3, direction: 12, opacity: 0.62, grain: true },
          layers: [
            { id: "background", gradient: "linear-gradient(180deg, #07090f 0%, #18212b 55%, #151815 100%)", width: 120, height: 120, x: -10, y: -10, depth: 0.05 },
            { id: "window-light", gradient: "radial-gradient(circle at 50% 50%, rgba(75,166,160,0.6), rgba(75,166,160,0.12) 34%, transparent 64%)", width: 58, height: 58, x: 12, y: 22, opacity: 0.72, depth: 0.25, blur: 1.4 },
            { id: "verticals", gradient: "repeating-linear-gradient(90deg, rgba(0,0,0,0.8) 0 18px, transparent 18px 88px)", width: 125, height: 120, x: -8, y: -8, opacity: 0.55, depth: 0.55 },
            { id: "foreground-shadow", gradient: "radial-gradient(circle at 70% 80%, transparent 0 20%, rgba(0,0,0,0.86) 62%)", width: 120, height: 120, x: -10, y: -10, depth: 0.95 }
          ],
          beats: [
            { id: "beat-open", type: "text", text: { mode: "narration", text: "The same engine can hold a shot while text, weather, and camera intent change.", placement: "upper", align: "left", staggerMs: 20, maxWidth: 660 } },
            { id: "beat-atmosphere", type: "atmosphere", atmosphere: { kind: "embers", density: 45, speed: 0.2, wind: 0.1, opacity: 0.7 } },
            { id: "beat-last", type: "text", text: { mode: "aether", text: "This is not the story. It is the instrument panel.", placement: "lower", align: "center", staggerMs: 35, durationMs: 900, maxWidth: 720 } }
          ]
        }
      ]
    }
  ]
};
