import { useEffect, useRef, useState, type CSSProperties } from "react";
import type { ProblemBox } from "../types";

interface Size {
  width: number;
  height: number;
}

interface PhotoWithBoxProps {
  src: string;
  box: ProblemBox | null;
  alt: string;
}

/** A photo shown with object-fit: contain, plus the AI's red box drawn exactly on top of it. */
export function PhotoWithBox({ src, box, alt }: PhotoWithBoxProps) {
  const frameRef = useRef<HTMLDivElement>(null);
  const [frame, setFrame] = useState<Size>({ width: 0, height: 0 });
  const [natural, setNatural] = useState<Size>({ width: 0, height: 0 });

  useEffect(() => {
    const element = frameRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) =>
      setFrame({ width: entry.contentRect.width, height: entry.contentRect.height }),
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const ready = box !== null && natural.width > 0 && frame.width > 0;
  return (
    <div ref={frameRef} className="photo-frame">
      <img
        src={src}
        alt={alt}
        onLoad={(event) =>
          setNatural({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })
        }
      />
      {ready && <div className="problem-box" style={boxPosition(box, natural, frame)} />}
    </div>
  );
}

/** Where a 0–1000 box lands on an image scaled with object-fit: contain inside `frame`. */
function boxPosition(box: ProblemBox, natural: Size, frame: Size): CSSProperties {
  const scale = Math.min(frame.width / natural.width, frame.height / natural.height);
  const shownWidth = natural.width * scale;
  const shownHeight = natural.height * scale;
  const offsetX = (frame.width - shownWidth) / 2;
  const offsetY = (frame.height - shownHeight) / 2;
  const [ymin, xmin, ymax, xmax] = box;
  return {
    left: offsetX + (xmin / 1000) * shownWidth,
    top: offsetY + (ymin / 1000) * shownHeight,
    width: ((xmax - xmin) / 1000) * shownWidth,
    height: ((ymax - ymin) / 1000) * shownHeight,
  };
}
