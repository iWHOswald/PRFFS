import { useEffect, useRef } from "react";
import type { AtmosphereConfig } from "../types";

type Particle = {
  x: number;
  y: number;
  size: number;
  speed: number;
  opacity: number;
  depth: number;
  drift: number;
  phase: number;
};

export function Atmosphere({ config, active }: { config?: AtmosphereConfig; active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !config || config.kind === "none") return undefined;
    const activeConfig = config;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return undefined;

    const context = canvas.getContext("2d");
    if (!context) return undefined;
    const ctx = context;
    const cnv = canvas;

    let width = 0;
    let height = 0;
    let frame = 0;
    let last = performance.now();
    let particles: Particle[] = [];

    function resize() {
      const rect = cnv.getBoundingClientRect();
      const ratio = Math.min(2, window.devicePixelRatio || 1);
      width = Math.max(1, Math.floor(rect.width * ratio));
      height = Math.max(1, Math.floor(rect.height * ratio));
      cnv.width = width;
      cnv.height = height;
      particles = createParticles(activeConfig, width, height);
    }

    function draw(now: number) {
      frame = window.requestAnimationFrame(draw);
      if (!active || document.hidden) {
        last = now;
        return;
      }
      const dt = Math.min(50, now - last) / 16.67;
      last = now;
      ctx.clearRect(0, 0, width, height);
      const gust = Math.sin(now / 2600) * (activeConfig.gustiness ?? 0.2);
      for (const particle of particles) {
        updateParticle(particle, activeConfig, width, height, dt, gust);
        renderParticle(ctx, particle, activeConfig, now);
      }
    }

    resize();
    window.addEventListener("resize", resize);
    frame = window.requestAnimationFrame(draw);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
    };
  }, [active, config]);

  return (
    <>
      {config?.kind === "fog" ? <div className="story-fog" /> : null}
      <canvas className="story-atmosphere" ref={canvasRef} aria-hidden="true" />
      {config?.grain ? <div className="story-grain" aria-hidden="true" /> : null}
    </>
  );
}

function createParticles(config: AtmosphereConfig, width: number, height: number): Particle[] {
  const density = config.density ?? 70;
  const multiplier = config.kind === "rain" ? 1.4 : 1;
  return Array.from({ length: Math.floor(density * multiplier) }, () => {
    const depth = Math.random();
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      size: (config.sizeMin ?? 1) + Math.random() * ((config.sizeMax ?? 4) - (config.sizeMin ?? 1)) * (0.55 + depth),
      speed: (config.speed ?? 0.4) * (0.5 + depth * 1.7),
      opacity: (config.opacity ?? 0.65) * (0.25 + depth * 0.75),
      depth,
      drift: (Math.random() - 0.5) * 0.8,
      phase: Math.random() * Math.PI * 2
    };
  });
}

function updateParticle(particle: Particle, config: AtmosphereConfig, width: number, height: number, dt: number, gust: number) {
  const wind = ((config.wind ?? 0) + gust + particle.drift) * (0.45 + particle.depth);
  const turbulence = Math.sin(performance.now() / 900 + particle.phase) * (config.turbulence ?? 0.2);
  particle.x += (wind + turbulence) * dt * 1.8;
  particle.y += particle.speed * dt * (config.kind === "rain" ? 14 : config.kind === "embers" ? -2.3 : 3.4);
  if (particle.y > height + 20) particle.y = -20;
  if (particle.y < -24) particle.y = height + 20;
  if (particle.x > width + 30) particle.x = -30;
  if (particle.x < -30) particle.x = width + 30;
}

function renderParticle(context: CanvasRenderingContext2D, particle: Particle, config: AtmosphereConfig, now: number) {
  context.save();
  context.globalAlpha = particle.opacity;
  if (config.kind === "rain") {
    context.strokeStyle = "rgba(210,230,240,0.75)";
    context.lineWidth = Math.max(1, particle.size * 0.42);
    context.beginPath();
    context.moveTo(particle.x, particle.y);
    context.lineTo(particle.x - (config.direction ?? 10) * particle.depth, particle.y + 14 + particle.depth * 22);
    context.stroke();
  } else if (config.kind === "embers") {
    const glow = 0.45 + Math.sin(now / 300 + particle.phase) * 0.3;
    context.fillStyle = `rgba(242,142,62,${glow})`;
    context.shadowColor = "rgba(242,142,62,0.7)";
    context.shadowBlur = particle.size * 4;
    context.beginPath();
    context.arc(particle.x, particle.y, particle.size * 0.9, 0, Math.PI * 2);
    context.fill();
  } else {
    context.fillStyle = config.kind === "dust" ? "rgba(226,214,176,0.6)" : "rgba(245,250,252,0.85)";
    if (config.kind === "snow" && config.motionBlur) {
      const length = config.motionBlur * (0.45 + particle.depth * 1.7);
      const wind = (config.wind ?? 0) * 32;
      context.strokeStyle = "rgba(245,250,252,0.72)";
      context.lineWidth = Math.max(1, particle.size * 0.72);
      context.lineCap = "round";
      context.shadowColor = "rgba(143,226,232,0.38)";
      context.shadowBlur = Math.max(0, particle.size * 1.8);
      context.beginPath();
      context.moveTo(particle.x, particle.y);
      context.lineTo(particle.x + wind - length * 0.45, particle.y + length);
      context.stroke();
    } else {
      context.beginPath();
      context.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      context.fill();
    }
  }
  context.restore();
}
