import { useEffect, useState, type RefObject } from "react";
import type { ProblemBox } from "../types";
import { boxPosition, type Size } from "./PhotoWithBox";

interface LiveBoxOverlayProps {
  videoRef: RefObject<HTMLVideoElement | null>;
  box: ProblemBox;
}

/**
 * The AI's red box drawn over the running video. Checks only happen on a steady scene
 * (camera on a stand), so the box still lines up until something moves, and then
 * the station clears it.
 */
export function LiveBoxOverlay({ videoRef, box }: LiveBoxOverlayProps) {
  const [frame, setFrame] = useState<Size>({ width: 0, height: 0 });
  const [natural, setNatural] = useState<Size>({ width: 0, height: 0 });

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const measure = () => {
      setFrame({ width: video.clientWidth, height: video.clientHeight });
      setNatural({ width: video.videoWidth, height: video.videoHeight });
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(video);
    video.addEventListener("loadedmetadata", measure);
    return () => {
      observer.disconnect();
      video.removeEventListener("loadedmetadata", measure);
    };
  }, [videoRef]);

  if (!natural.width || !frame.width) return null;
  return <div className="problem-box" style={boxPosition(box, natural, frame)} />;
}
