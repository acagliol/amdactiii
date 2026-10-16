import { useRef, type ChangeEvent } from "react";
import type { VideoSource } from "../hooks/useVideoSource";

interface SourceControlsProps {
  source: VideoSource;
  autoCheck: boolean;
  onToggleAuto: (on: boolean) => void;
}

/** Choose where frames come from (live camera or a recorded video) and whether checks run by themselves. */
export function SourceControls({ source, autoCheck, onToggleAuto }: SourceControlsProps) {
  const videoInput = useRef<HTMLInputElement>(null);

  function pickVideo(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow picking the same file again
    if (file) source.loadVideo(file);
  }

  return (
    <div className="source-bar">
      <div className="segmented" role="group" aria-label="Video source">
        <button className={source.kind === "camera" ? "segment active" : "segment"} onClick={source.switchToCamera}>
          📷 Live camera
        </button>
        <button className={source.kind === "video" ? "segment active" : "segment"} onClick={source.switchToVideo}>
          🎞 Recorded video
        </button>
      </div>

      {source.kind === "camera" && source.cameras.length > 1 && (
        <select
          className="camera-picker"
          value={source.cameraId}
          onChange={(event) => source.setCameraId(event.target.value)}
          aria-label="Camera"
        >
          <option value="">Default camera</option>
          {source.cameras.map((camera) => (
            <option key={camera.deviceId} value={camera.deviceId}>
              {camera.label}
            </option>
          ))}
        </select>
      )}

      {source.kind === "video" && (
        <>
          <button className="button button-ghost" onClick={() => videoInput.current?.click()}>
            {source.videoName ? "Choose another video" : "Choose video…"}
          </button>
          {source.videoName && (
            <button className="button button-ghost" onClick={source.togglePlay}>
              {source.status === "playing" ? "⏸ Pause" : source.status === "ended" ? "↺ Replay" : "▶ Play"}
            </button>
          )}
          <input ref={videoInput} type="file" accept="video/*" hidden onChange={pickVideo} />
        </>
      )}

      <label className="auto-toggle">
        <input type="checkbox" checked={autoCheck} onChange={(event) => onToggleAuto(event.target.checked)} />
        Auto-check when steady
      </label>
    </div>
  );
}
