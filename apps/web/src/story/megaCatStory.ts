import type { Story, StoryLayer } from "./types";

const assetRoot = "/story-assets/mega-cat/years-of-ash";

const oracleLayers: StoryLayer[] = [
  {
    id: "oracle-headquarters",
    asset: `${assetRoot}/bg-oracle-headquarters-cyberpunk-01.png`,
    width: 100,
    height: 100,
    depth: 0.12,
    blur: 0.9,
    brightness: 0.94,
    contrast: 1.05,
    saturation: 1.08
  },
  {
    id: "snow-glow",
    gradient: "radial-gradient(circle at 38% 62%, rgba(77, 211, 219, 0.2), transparent 34%), radial-gradient(circle at 77% 44%, rgba(245, 181, 91, 0.1), transparent 28%)",
    width: 100,
    height: 100,
    opacity: 0.64,
    depth: 0.2,
    blendMode: "screen"
  },
  {
    id: "security-perimeter",
    asset: `${assetRoot}/mg-security-perimeter-alpha-01.png`,
    fit: "cover",
    width: 100,
    height: 100,
    y: 0.1,
    opacity: 0.78,
    depth: 0.48,
    blur: 0.18,
    brightness: 1.05,
    saturation: 1.12
  }
];

const megaCatLayer: StoryLayer = {
  id: "mega-cat",
  asset: `${assetRoot}/fg-mega-cat-cyberpunk-alpha-01.png`,
  fit: "contain",
  width: 30,
  height: 82,
  x: 12,
  y: 20,
  depth: 0.82,
  brightness: 1.05,
  contrast: 1.08,
  saturation: 1.08
};

export const megaCatStory: Story = {
  id: "mega-cat-championship",
  title: "Mega Cat: The Years of Ash",
  chapters: [
    {
      id: "chapter-01",
      title: "The Years of Ash",
      scenes: [
        {
          id: "001-oracle",
          title: "The Office",
          overscan: 10,
          camera: {
            keyframes: [
              { at: 0, x: 1.5, y: 0, scale: 1.04, originX: 48, originY: 52 },
              { at: 26, x: -2.5, y: -1.5, scale: 1.12, originX: 48, originY: 52 }
            ],
            easing: "cinematic"
          },
          atmosphere: { kind: "snow", density: 118, speed: 0.52, wind: -0.2, gustiness: 0.34, opacity: 0.78, sizeMin: 1, sizeMax: 4.6, motionBlur: 15, grain: true },
          bloom: [
            { id: "drone-left", x: 13, y: 23, size: 18, opacity: 0.34, color: "111, 230, 238", stretch: 3.4 },
            { id: "gate", x: 51, y: 70, size: 26, opacity: 0.28, color: "77, 211, 219", stretch: 2.2 },
            { id: "amber-archive", x: 62, y: 47, size: 16, opacity: 0.18, color: "245, 181, 91", stretch: 1.9 }
          ],
          layers: oracleLayers,
          beats: [
            {
              id: "title",
              type: "text",
              text: { mode: "title", text: "THE YEARS OF ASH", placement: "center", align: "center", staggerMs: 28, durationMs: 820, maxWidth: 920 }
            },
            {
              id: "jurisdiction",
              type: "text",
              text: { mode: "aether", text: "The league kept its records in a cold office at the edge of the standings.", placement: "lower", align: "left", staggerMs: 22, durationMs: 720, maxWidth: 760 }
            },
            {
              id: "camera-gate",
              type: "camera",
              action: {
                keyframes: [
                  { at: 0, x: -3.5, y: 0.5, scale: 1.08, originX: 43, originY: 58 },
                  { at: 24, x: -6.5, y: -1.2, scale: 1.2, originX: 43, originY: 58 }
                ],
                easing: "dramaticPush"
              }
            },
            {
              id: "dumpster",
              type: "text",
              text: { mode: "narration", text: "Dumpster was not a nickname. It was a filing status.", placement: "lower", align: "left", staggerMs: 20, durationMs: 720, maxWidth: 640 }
            }
          ]
        },
        {
          id: "002-mega-cat-arrives",
          title: "Mega Cat Arrives",
          overscan: 12,
          camera: {
            keyframes: [
              { at: 0, x: 1.5, y: 0, scale: 1.05, originX: 38, originY: 65 },
              { at: 24, x: -4.5, y: -1, scale: 1.15, originX: 38, originY: 65 }
            ],
            easing: "cinematic"
          },
          atmosphere: { kind: "snow", density: 136, speed: 0.58, wind: -0.24, gustiness: 0.42, opacity: 0.82, sizeMin: 1, sizeMax: 4.8, motionBlur: 18, grain: true },
          bloom: [
            { id: "left-flood", x: 16, y: 36, size: 19, opacity: 0.32, color: "132, 236, 241", stretch: 3.8 },
            { id: "cat-rim", x: 28, y: 51, size: 15, opacity: 0.2, color: "77, 211, 219", stretch: 2.4 },
            { id: "building-core", x: 56, y: 46, size: 22, opacity: 0.22, color: "245, 181, 91", stretch: 2 }
          ],
          layers: [...oracleLayers, megaCatLayer],
          beats: [
            {
              id: "arrives",
              type: "text",
              text: { mode: "aether", text: "Then James Oswald walked into the archive wearing the old joke like credentials.", placement: "lower", align: "left", staggerMs: 19, durationMs: 720, maxWidth: 760 }
            },
            {
              id: "camera-close",
              type: "camera",
              action: {
                keyframes: [
                  { at: 0, x: -2, y: 0, scale: 1.09, originX: 27, originY: 62 },
                  { at: 22, x: -10, y: -2, scale: 1.28, originX: 27, originY: 62 }
                ],
                easing: "dramaticPush"
              }
            },
            {
              id: "mega-cat",
              type: "text",
              text: { mode: "dialogue", speaker: "MEGA CAT", text: "Pull the 2023 file.", placement: "right", align: "right", staggerMs: 32, durationMs: 620, maxWidth: 520 }
            }
          ]
        },
        {
          id: "003-record",
          title: "The Record",
          overscan: 12,
          camera: {
            keyframes: [
              { at: 0, x: -5, y: -1, scale: 1.14, originX: 50, originY: 50 },
              { at: 26, x: 1.5, y: -2.2, scale: 1.24, originX: 64, originY: 46 }
            ],
            easing: "slowEase"
          },
          atmosphere: { kind: "snow", density: 104, speed: 0.46, wind: -0.18, gustiness: 0.28, opacity: 0.7, sizeMin: 1, sizeMax: 4.2, motionBlur: 14, grain: true },
          bloom: [
            { id: "data-left", x: 35, y: 45, size: 18, opacity: 0.24, color: "77, 211, 219", stretch: 3.2 },
            { id: "data-right", x: 75, y: 42, size: 25, opacity: 0.22, color: "77, 211, 219", stretch: 3.6 },
            { id: "center-archive", x: 55, y: 70, size: 20, opacity: 0.18, color: "245, 181, 91", stretch: 2.1 }
          ],
          layers: [
            ...oracleLayers,
            {
              ...megaCatLayer,
              x: 9,
              y: 22,
              opacity: 0.92
            },
            {
              id: "data-wash",
              gradient: "linear-gradient(90deg, transparent 0 48%, rgba(77, 211, 219, 0.14) 56%, transparent 78%)",
              width: 100,
              height: 100,
              opacity: 0.72,
              depth: 0.9,
              blendMode: "screen"
            }
          ],
          beats: [
            {
              id: "record-open",
              type: "text",
              text: { mode: "narration", text: "The database did not care about dignity. It cared about rows.", placement: "upper", align: "left", staggerMs: 22, durationMs: 720, maxWidth: 660 }
            },
            {
              id: "championship",
              type: "text",
              text: { mode: "aether", text: "In 2023, the division everyone mocked produced the champion.", placement: "lower", align: "left", staggerMs: 22, durationMs: 760, maxWidth: 720 }
            },
            {
              id: "margin",
              type: "text",
              text: { mode: "hardCut", text: "By 0.33 points.", placement: "center", align: "center", durationMs: 520, maxWidth: 760 }
            }
          ]
        }
      ]
    }
  ]
};
