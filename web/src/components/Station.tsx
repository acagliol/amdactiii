import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { api } from "../api";
import { errorMessage } from "../format";
import { useCamera } from "../hooks/useCamera";
import { useElapsedSeconds } from "../hooks/useElapsedSeconds";
import type { ActionResponse, CheckResult, UnitState } from "../types";
import { CaptureStage, type Phase } from "./CaptureStage";
import { GatePanel } from "./GatePanel";
import { ManualPanel } from "./ManualPanel";
import { OverrideDialog } from "./OverrideDialog";
import { ReferencePanel } from "./ReferencePanel";
import { ResultCard } from "./ResultCard";
import { StepList } from "./StepList";

const AUTO_CONTINUE_MS = 1800; // after a Pass, show the green ring briefly, then go to the next step

interface StationProps {
  unit: UnitState;
  modelName: string;
  onUnitChange: (unit: UnitState) => void;
}

/** One unit in progress: steps on the left, camera/action in the middle, the step's details on the right. */
export function Station({ unit, modelName, onUnitChange }: StationProps) {
  const camera = useCamera();
  const [phase, setPhase] = useState<Phase>("live");
  const [frozenUrl, setFrozenUrl] = useState<string | null>(null);
  const [result, setResult] = useState<CheckResult | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [overrideOpen, setOverrideOpen] = useState(false);
  const uploadInput = useRef<HTMLInputElement>(null);
  const elapsedSeconds = useElapsedSeconds(phase === "checking");
  const current = unit.current;

  // Free the frozen photo's memory when it is replaced.
  useEffect(() => () => void (frozenUrl && URL.revokeObjectURL(frozenUrl)), [frozenUrl]);

  // After a Pass, move on automatically.
  useEffect(() => {
    if (phase !== "result" || result?.action !== "pass") return;
    const timer = window.setTimeout(backToCamera, AUTO_CONTINUE_MS);
    return () => window.clearTimeout(timer);
  }, [phase, result]);

  function backToCamera() {
    setPhase("live");
    setResult(null);
    setFrozenUrl(null);
  }

  async function checkPhoto(photo: Blob, fileName: string) {
    setError(null);
    setNotice(null);
    setFrozenUrl(URL.createObjectURL(photo));
    setPhase("checking");
    try {
      const response = await api.checkPhoto(unit.unit_id, photo, fileName);
      onUnitChange(response.unit);
      setResult(response.result);
      setPhase("result");
    } catch (e) {
      setError(errorMessage(e));
      backToCamera();
    }
  }

  async function captureAndCheck() {
    const frame = await camera.captureFrame();
    if (frame) await checkPhoto(frame, "camera_capture.jpg");
    else setError("The camera isn't ready. Wait a moment, or upload a photo.");
  }

  function uploadAndCheck(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow picking the same file again
    if (file) void checkPhoto(file, file.name);
  }

  /** Manual confirm, gate, and override: no photo, so show the outcome as a short notice. */
  async function runStepAction(request: () => Promise<ActionResponse>) {
    setError(null);
    setBusy(true);
    try {
      const response = await request();
      onUnitChange(response.unit);
      setNotice(`${response.result.action === "pass" ? "✓" : "!"} ${response.result.reason}`);
      setOverrideOpen(false);
      backToCamera();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  if (!current) return null; // the unit is complete; App shows the completion screen

  // Keep the camera area while a photo is being checked or its result is shown,
  // even if the unit has already advanced to a manual or gate step.
  const showCamera = current.kind === "visual" || phase !== "live";

  return (
    <main className="station">
      <StepList steps={unit.steps} />

      <section className="workspace">
        {error && <p className="error banner">{error}</p>}
        {notice && phase === "live" && <p className="notice banner">{notice}</p>}

        {showCamera && (
          <>
            {current.hides && phase === "live" && (
              <p className="notice banner">🔓 This step covers earlier work. Unlocked because all its checks passed.</p>
            )}
            <CaptureStage
              phase={phase}
              videoRef={camera.videoRef}
              cameraStatus={camera.status}
              cameraMessage={camera.message}
              frozenUrl={frozenUrl}
              result={result}
              elapsedSeconds={elapsedSeconds}
              modelName={modelName}
            />

            {phase === "result" && result ? (
              <ResultCard result={result} onRetake={backToCamera} onContinue={backToCamera} onOverride={() => setOverrideOpen(true)} />
            ) : (
              <div className="capture-actions">
                <button
                  className="button button-primary button-large"
                  disabled={phase === "checking" || camera.status !== "live"}
                  onClick={captureAndCheck}
                >
                  {phase === "checking" ? "Checking…" : "Check"}
                </button>
                <button className="button button-ghost" disabled={phase === "checking"} onClick={() => uploadInput.current?.click()}>
                  Upload photo
                </button>
                <input ref={uploadInput} type="file" accept="image/jpeg,image/png" hidden onChange={uploadAndCheck} />
              </div>
            )}
          </>
        )}

        {!showCamera && current.kind === "manual" && (
          <ManualPanel check={current} busy={busy} onConfirm={(ok, note) => runStepAction(() => api.confirmManual(unit.unit_id, ok, note))} />
        )}

        {!showCamera && current.kind === "gate" && (
          <GatePanel check={current} busy={busy} onConfirm={() => runStepAction(() => api.confirmGate(unit.unit_id))} />
        )}
      </section>

      <ReferencePanel check={current} />

      {overrideOpen && (
        <OverrideDialog
          busy={busy}
          onCancel={() => setOverrideOpen(false)}
          onSubmit={(reason) => runStepAction(() => api.override(unit.unit_id, reason))}
        />
      )}
    </main>
  );
}
