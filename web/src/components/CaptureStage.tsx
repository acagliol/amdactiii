import type { RefObject } from "react";
import { ACTION_LABEL } from "../format";
import type { WatcherView } from "../hooks/useSceneWatcher";
import type { SourceKind, SourceStatus } from "../hooks/useVideoSource";
import type { CheckResult } from "../types";
import { LiveBoxOverlay } from "./LiveBoxOverlay";
import { LogoMark } from "./Logo";
import { PhotoWithBox } from "./PhotoWithBox";

export type Phase = "live" | "checking" | "result";

interface CaptureStageProps {
  phase: Phase; // "checking"/"result" = a manual check with the frame frozen on screen
  videoRef: RefObject<HTMLVideoElement | null>;
  sourceKind: SourceKind;
  sourceStatus: SourceStatus;
  sourceMessage: string | null;
  frozenUrl: string | null;
  result: CheckResult | null; // result of a manual check
  liveResult: CheckResult | null; // result of an auto-check, drawn over the running video
  autoCheck: boolean;
  autoChecking: boolean;
  watcher: WatcherView;
  elapsedSeconds: number;
  modelName: string;
}

/**
 * The camera area. The video always stays mounted (so the camera keeps running).
 * Auto-checks keep the video running and draw the result on top of it; a manual
 * Check freezes the photo on screen until the worker continues.
 */
export function CaptureStage(props: CaptureStageProps) {
  const { phase, videoRef, frozenUrl, result, liveResult, autoChecking, elapsedSeconds, modelName } = props;
  const showFrozen = phase !== "live" && frozenUrl !== null;
  const shownAction = phase === "result" ? result?.action : phase === "live" ? liveResult?.action : undefined;
  const placeholder = stagePlaceholder(props.sourceKind, props.sourceStatus, props.sourceMessage);

  return (
    <div className={`stage ${shownAction ? `stage-${shownAction}` : ""}`}>
      <video ref={videoRef} className="stage-video" muted playsInline />

      {phase === "live" && placeholder && (
        <div className="stage-message">
          <LogoMark size={56} />
          <p>{placeholder}</p>
        </div>
      )}

      {phase === "live" && !placeholder && <StatusPill {...props} />}

      {phase === "live" && liveResult?.problem_box && <LiveBoxOverlay videoRef={videoRef} box={liveResult.problem_box} />}

      {phase === "live" && liveResult && (
        <div className={`live-banner live-banner-${liveResult.action}`} aria-live="polite">
          <LogoMark size={34} state={liveResult.action} />
          <span className={`badge badge-${liveResult.action}`}>{ACTION_LABEL[liveResult.action]}</span>
          <span className="live-banner-reason">{liveResult.reason}</span>
        </div>
      )}

      {autoChecking && (
        <div className="checking-chip">
          <LogoMark size={22} state="checking" />
          Checking with {modelName}… <span className="mono">{elapsedSeconds}s</span>
        </div>
      )}

      {showFrozen && (
        <div className="stage-frozen">
          <PhotoWithBox src={frozenUrl} box={phase === "result" ? (result?.problem_box ?? null) : null} alt="Checked photo" />
        </div>
      )}

      {phase === "checking" && (
        <div className="stage-checking">
          <LogoMark size={92} state="checking" />
          <p>
            Checking with {modelName}… <span className="mono">{elapsedSeconds}s</span>
          </p>
        </div>
      )}
    </div>
  );
}

/** Text shown instead of the video when there is nothing to show yet. */
function stagePlaceholder(kind: SourceKind, status: SourceStatus, message: string | null): string | null {
  if (kind === "camera" && status === "starting") return "Starting camera…";
  if (kind === "camera" && status === "unavailable") return message;
  if (kind === "video" && status === "no-video") return "Choose a recorded video of the assembly. Each steady moment is checked in order.";
  return null;
}

/** Top-left status: what the watcher sees right now (instant, no AI involved). */
function StatusPill({ sourceKind, sourceStatus, autoCheck, autoChecking, watcher }: CaptureStageProps) {
  if (autoChecking) return null; // the checking chip says enough
  if (sourceKind === "video" && sourceStatus === "ended") {
    return <span className="stage-tag">Video finished</span>;
  }
  if (sourceKind === "video" && sourceStatus === "paused") {
    return <span className="stage-tag">⏸ Paused</span>;
  }
  if (!autoCheck) {
    return <span className="stage-tag stage-tag-live">{sourceKind === "camera" ? "● Live" : "▶ Playing"}</span>;
  }

  const labels: Record<WatcherView["state"], string> = {
    idle: sourceKind === "camera" ? "● Live" : "▶ Playing",
    dark: "Too dark: add light",
    moving: "Hold still…",
    settling: "Steady…",
    "waiting-change": "✓ Checked · watching for changes",
    ready: "Steady ✓",
  };
  return (
    <span className={`stage-tag watch-${watcher.state}`}>
      {labels[watcher.state]}
      {watcher.state === "settling" && (
        <span className="watch-progress">
          <span style={{ width: `${Math.round(watcher.progress * 100)}%` }} />
        </span>
      )}
    </span>
  );
}
