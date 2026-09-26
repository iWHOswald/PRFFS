import { motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type RefObject } from "react";
import { Swiper, SwiperRef, SwiperSlide } from "swiper/react";
import "swiper/css";
import { cameraAnimation } from "../camera";
import type { AtmosphereConfig, Beat, BloomFlare, CameraConfig, Scene, Story } from "../types";
import { Atmosphere } from "./Atmosphere";
import { LayerRenderer } from "./LayerRenderer";
import { NavigationHUD } from "./NavigationHUD";
import { TextReveal } from "./TextReveal";
import { useAudioManager } from "./AudioManager";

export function StoryPlayer({ story, onExit }: { story: Story; onExit?: () => void }) {
  const scenes = story.chapters.flatMap((chapter) => chapter.scenes);
  const stageRef = useRef<HTMLElement>(null);
  const swiperRef = useRef<SwiperRef>(null);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [beatIndex, setBeatIndex] = useState(0);
  const [forceCompleteText, setForceCompleteText] = useState(false);
  const [textComplete, setTextComplete] = useState(false);
  const [hudActive, setHudActive] = useState(true);
  const idleTimer = useRef<number>();
  const scene = scenes[sceneIndex] ?? scenes[0];
  const activeBeat = scene?.beats[beatIndex];
  const { muted, setMuted } = useAudioManager(activeBeat);

  const camera = useMemo(() => activeCamera(scene, beatIndex), [beatIndex, scene]);
  const atmosphere = useMemo(() => activeAtmosphere(scene, beatIndex), [beatIndex, scene]);

  const next = useCallback(() => {
    if (activeBeat?.type === "text" && !textComplete) {
      setForceCompleteText(true);
      return;
    }
    setForceCompleteText(false);
    setTextComplete(false);
    if (beatIndex < scene.beats.length - 1) {
      setBeatIndex(beatIndex + 1);
      return;
    }
    if (sceneIndex < scenes.length - 1) {
      swiperRef.current?.swiper.slideNext();
      setSceneIndex(sceneIndex + 1);
      setBeatIndex(0);
    }
  }, [activeBeat, beatIndex, scene.beats.length, sceneIndex, scenes.length, textComplete]);

  const previous = useCallback(() => {
    setForceCompleteText(false);
    setTextComplete(true);
    if (beatIndex > 0) {
      setBeatIndex(beatIndex - 1);
      return;
    }
    if (sceneIndex > 0) {
      swiperRef.current?.swiper.slidePrev();
      const previousScene = scenes[sceneIndex - 1];
      setSceneIndex(sceneIndex - 1);
      setBeatIndex(Math.max(0, previousScene.beats.length - 1));
    }
  }, [beatIndex, sceneIndex, scenes]);

  useKeyControls(next, previous, stageRef);

  const showHud = useCallback(() => {
    setHudActive(true);
    if (idleTimer.current) window.clearTimeout(idleTimer.current);
    idleTimer.current = window.setTimeout(() => setHudActive(false), 1800);
  }, []);

  return (
    <section className={hudActive ? "story-stage is-hud-active" : "story-stage"} ref={stageRef} onMouseMove={showHud} onTouchStart={showHud}>
      <Swiper
        ref={swiperRef}
        className="story-swiper"
        slidesPerView={1}
        allowTouchMove
        onSlideChange={(swiper) => {
          setSceneIndex(swiper.activeIndex);
          setBeatIndex(0);
          setForceCompleteText(false);
          setTextComplete(false);
        }}
      >
        {scenes.map((item, index) => (
          <SwiperSlide key={item.id}>
            <StoryScene scene={item} active={index === sceneIndex} camera={index === sceneIndex ? camera : item.camera} atmosphere={index === sceneIndex ? atmosphere : item.atmosphere} activeBeat={index === sceneIndex ? activeBeat : undefined} forceCompleteText={forceCompleteText} onTextComplete={() => setTextComplete(true)} />
          </SwiperSlide>
        ))}
      </Swiper>
      {onExit ? <button className="story-exit" type="button" onClick={onExit}>League Ops</button> : null}
      <NavigationHUD sceneIndex={sceneIndex} sceneCount={scenes.length} beatIndex={beatIndex} beatCount={scene.beats.length} muted={muted} setMuted={setMuted} stageRef={stageRef} onPrevious={previous} onNext={next} />
    </section>
  );
}

function StoryScene({ scene, active, camera, atmosphere, activeBeat, forceCompleteText, onTextComplete }: { scene: Scene; active: boolean; camera?: CameraConfig; atmosphere?: AtmosphereConfig; activeBeat?: Beat; forceCompleteText: boolean; onTextComplete: () => void }) {
  const overscan = scene.overscan ?? 12;
  const animation = active ? cameraAnimation(camera) : { animate: {}, transition: {} };
  return (
    <div className="story-scene" aria-label={scene.title}>
      <motion.div
        className="story-camera"
        animate={animation.animate}
        transition={animation.transition}
        style={{
          inset: `${-overscan}%`,
          width: `${100 + overscan * 2}%`,
          height: `${100 + overscan * 2}%`
        }}
      >
        <LayerRenderer layers={scene.layers} />
      </motion.div>
      <Atmosphere config={atmosphere} active={active} />
      <BloomLayer flares={scene.bloom ?? []} />
      <div className="story-vignette" />
      {activeBeat?.type === "text" ? <TextReveal key={activeBeat.id} text={activeBeat.text} forceComplete={forceCompleteText} onComplete={onTextComplete} /> : null}
    </div>
  );
}

function BloomLayer({ flares }: { flares: BloomFlare[] }) {
  if (!flares.length) return null;
  return (
    <div className="story-bloom" aria-hidden="true">
      {flares.map((flare) => (
        <span
          key={flare.id}
          style={{
            "--flare-x": `${flare.x}%`,
            "--flare-y": `${flare.y}%`,
            "--flare-size": `${flare.size}vmax`,
            "--flare-opacity": flare.opacity ?? 0.55,
            "--flare-color": flare.color ?? "77, 211, 219",
            "--flare-stretch": flare.stretch ?? 2.8
          } as CSSProperties}
        />
      ))}
    </div>
  );
}

function activeCamera(scene: Scene, beatIndex: number): CameraConfig | undefined {
  let camera = scene.camera;
  for (const beat of scene.beats.slice(0, beatIndex + 1)) {
    if (beat.type === "camera") camera = beat.action;
  }
  return camera;
}

function activeAtmosphere(scene: Scene, beatIndex: number): AtmosphereConfig | undefined {
  let atmosphere = scene.atmosphere;
  for (const beat of scene.beats.slice(0, beatIndex + 1)) {
    if (beat.type === "atmosphere") atmosphere = { ...(atmosphere ?? { kind: "none" }), ...beat.atmosphere } as AtmosphereConfig;
  }
  return atmosphere;
}

function useKeyControls(next: () => void, previous: () => void, stageRef: RefObject<HTMLElement>) {
  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if (event.key === "ArrowRight") next();
      if (event.key === "ArrowLeft") previous();
      if (event.key.toLowerCase() === "f") {
        if (document.fullscreenElement) document.exitFullscreen().catch(() => undefined);
        else stageRef.current?.requestFullscreen?.().catch(() => undefined);
      }
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, [next, previous, stageRef]);
}
