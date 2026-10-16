import { useEffect, useRef, useState, type RefObject } from "react";
import { newWatchMemory, WATCHER, watchStep, type WatchView } from "./sceneWatcherLogic";

export type { WatchState } from "./sceneWatcherLogic";
export type WatcherView = WatchView;

interface WatcherOptions {
  enabled: boolean;
  busy: boolean; // a check is running; never start another
  stepKey: string; // the current check id
  onSettled: () => void; // called when the scene settled and changed: check it now
}

/** Samples the video 5 times a second and applies the watcher's rules (sceneWatcherLogic.ts). */
export function useSceneWatcher(videoRef: RefObject<HTMLVideoElement | null>, options: WatcherOptions): WatcherView {
  const [view, setView] = useState<WatcherView>({ state: "idle", progress: 0 });
  const optionsRef = useRef(options);
  optionsRef.current = options;

  useEffect(() => {
    const memory = newWatchMemory();
    const canvas = document.createElement("canvas");
    canvas.width = WATCHER.sampleWidth;
    canvas.height = WATCHER.sampleHeight;
    const context = canvas.getContext("2d", { willReadFrequently: true });

    const timer = window.setInterval(() => {
      const { enabled, busy, stepKey, onSettled } = optionsRef.current;
      const video = videoRef.current;
      const frameReady = video !== null && video.readyState >= 2 && video.videoWidth > 0 && context !== null;
      const decision = watchStep(memory, {
        enabled: enabled && video !== null,
        busy,
        stepKey,
        sample: frameReady ? sampleGray(video, context) : null,
        now: Date.now(),
      });
      if (!decision) return;
      setView((old) =>
        old.state === decision.state && Math.abs(old.progress - decision.progress) < 0.05
          ? old
          : { state: decision.state, progress: decision.progress },
      );
      if (decision.trigger) onSettled();
    }, WATCHER.sampleEveryMs);

    return () => window.clearInterval(timer);
  }, [videoRef]);

  return view;
}

/** A tiny greyscale copy of the current frame. */
function sampleGray(video: HTMLVideoElement, context: CanvasRenderingContext2D): Uint8Array {
  const { sampleWidth, sampleHeight } = WATCHER;
  context.drawImage(video, 0, 0, sampleWidth, sampleHeight);
  const rgba = context.getImageData(0, 0, sampleWidth, sampleHeight).data;
  const gray = new Uint8Array(sampleWidth * sampleHeight);
  for (let i = 0; i < gray.length; i++) {
    gray[i] = (rgba[i * 4] * 299 + rgba[i * 4 + 1] * 587 + rgba[i * 4 + 2] * 114) / 1000;
  }
  return gray;
}
