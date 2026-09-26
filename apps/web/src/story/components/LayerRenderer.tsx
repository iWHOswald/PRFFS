import { motion } from "framer-motion";
import type { StoryLayer } from "../types";

export function LayerRenderer({ layers, cameraX = 0, cameraY = 0 }: { layers: StoryLayer[]; cameraX?: number; cameraY?: number }) {
  return (
    <>
      {layers.filter((layer) => layer.visible !== false).map((layer) => {
        const depth = layer.depth ?? 0.5;
        const filters = [
          layer.blur ? `blur(${layer.blur}px)` : undefined,
          layer.brightness ? `brightness(${layer.brightness})` : undefined,
          layer.contrast ? `contrast(${layer.contrast})` : undefined,
          layer.saturation ? `saturate(${layer.saturation})` : undefined
        ].filter(Boolean).join(" ");
        return (
          <motion.div
            className="story-layer"
            key={layer.id}
            style={{
              background: layer.asset ? undefined : layer.gradient ?? layer.color,
              backgroundImage: layer.asset ? `url(${layer.asset})` : layer.gradient,
              backgroundPosition: "center",
              mixBlendMode: layer.blendMode,
              opacity: layer.opacity ?? 1,
              filter: filters || undefined,
              width: `${layer.width ?? 100}%`,
              height: `${layer.height ?? 100}%`,
              left: `${layer.x ?? 0}%`,
              top: `${layer.y ?? 0}%`,
              backgroundRepeat: layer.asset ? "no-repeat" : undefined,
              transform: `translate(${cameraX * depth}px, ${cameraY * depth}px) scale(${layer.scale ?? 1})`,
              backgroundSize: layer.asset ? layer.fit ?? "cover" : undefined,
              zIndex: Math.round(depth * 100)
            }}
          />
        );
      })}
    </>
  );
}
