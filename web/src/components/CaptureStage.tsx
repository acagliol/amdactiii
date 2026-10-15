import type { RefObject } from "react";
import type { CameraStatus } from "../hooks/useCamera";
import type { CheckResult } from "../types";
import { LogoMark } from "./Logo";
import { PhotoWithBox } from "./PhotoWithBox";

export type Phase = "live" | "checking" | "result";

interface CaptureStageProps {
  phase: Phase;
  videoRef: RefObject<HTMLVideoElement | null>;
  cameraStatus: CameraStatus;
  cameraMessage: string | null;
  frozenUrl: string | null;
  result: CheckResult | null;
  elapsedSeconds: number;
  modelName: string;
}

/**
 * The camera area. The live video stays mounted (so the camera keeps running),
 * and the frozen photo is laid over it while checking and while showing the result.
 */
export function CaptureStage(props: CaptureStageProps) {
  const { phase, videoRef, cameraStatus, cameraMessage, frozenUrl, result, elapsedSeconds, modelName } = props;
  const showFrozen = phase !== "live" && frozenUrl !== null;

  return (
    <div className={`stage stage-${phase} ${result && phase === "result" ? `stage-${result.action}` : ""}`}>
      <video ref={videoRef} className="stage-video" muted playsInline />

      {phase === "live" && cameraStatus !== "live" && (
        <div className="stage-message">
          <LogoMark size={56} />
          <p>{cameraStatus === "starting" ? "Starting camera…" : cameraMessage}</p>
        </div>
      )}

      {phase === "live" && cameraStatus === "live" && <span className="stage-tag stage-tag-live">● Live</span>}

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
