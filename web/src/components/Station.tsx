import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { api } from "../api";
import { errorMessage } from "../format";
import { useElapsedSeconds } from "../hooks/useElapsedSeconds";
import { useSceneWatcher } from "../hooks/useSceneWatcher";
import { useVideoSource } from "../hooks/useVideoSource";
import type { ActionResponse, CheckResult, UnitState } from "../types";
import { CaptureStage, type Phase } from "./CaptureStage";
import { CheckLog, type LogEntry } from "./CheckLog";
import { GatePanel } from "./GatePanel";
import { ManualPanel } from "./ManualPanel";
import { OverrideDialog } from "./OverrideDialog";
import { ReferencePanel } from "./ReferencePanel";
import { ResultCard } from "./ResultCard";
import { SourceControls } from "./SourceControls";
import { StepList } from "./StepList";

const AUTO_CONTINUE_MS = 1800; // manual check: after a Pass, show the green ring briefly, then continue
const LIVE_PASS_BANNER_MS = 2200; // auto-check: how long a Pass stays on top of the live video
const VIDEO_PAUSE_AFTER_PASS_MS = 1200; // recorded video: pause on each result so it can be read
const VIDEO_PAUSE_AFTER_PROBLEM_MS = 2600;

interface StationProps {
  unit: UnitState;
  modelName: string;
  onUnitChange: (unit: UnitState) => void;
}

/** One unit in progress: steps on the left, camera/action in the middle, the step's details on the right. */
export function Station({ unit, modelName, onUnitChange }: StationProps) {
  const source = useVideoSource();
  const [phase, setPhase] = useState<Phase>("live");
  const [frozenUrl, setFrozenUrl] = useState<string | null>(null);
  const [result, setResult] = useState<CheckResult | null>(null);
  const [liveResult, setLiveResult] = useState<CheckResult | null>(null);
  const [autoCheck, setAutoCheck] = useState(true);
  const [autoChecking, setAutoChecking] = useState(false);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [overrideOpen, setOverrideOpen] = useState(false);
  const uploadInput = useRef<HTMLInputElement>(null);
  const autoCheckingRef = useRef(false); // blocks a second auto-check even before React re-renders
  const nextLogId = useRef(1);
  const elapsedSeconds = useElapsedSeconds(phase === "checking" || autoChecking);
  const current = unit.current;

  const sourceRunning = source.status === "live" || source.status === "playing";
  const watcher = useSceneWatcher(source.videoRef, {
    enabled: autoCheck && phase === "live" && current?.kind === "visual" && sourceRunning,
    busy: autoChecking,
    stepKey: current?.check_id ?? "",
    onSettled: () => void autoCheckNow(),
  });

  // Free the frozen photo's memory when it is replaced.
  useEffect(() => () => void (frozenUrl && URL.revokeObjectURL(frozenUrl)), [frozenUrl]);

  // Manual check: after a Pass, move on automatically.
  useEffect(() => {
    if (phase !== "result" || result?.action !== "pass") return;
    const timer = window.setTimeout(backToCamera, AUTO_CONTINUE_MS);
    return () => window.clearTimeout(timer);
  }, [phase, result]);

  // Auto-check: a Pass fades after a moment; any result clears once the scene moves again.
  useEffect(() => {
    if (liveResult?.action !== "pass") return;
    const timer = window.setTimeout(() => setLiveResult(null), LIVE_PASS_BANNER_MS);
    return () => window.clearTimeout(timer);
  }, [liveResult]);

  useEffect(() => {
    if (watcher.state === "moving") setLiveResult(null);
  }, [watcher.state]);

  function addToLog(at: string, checked: CheckResult) {
    const entry: LogEntry = { id: nextLogId.current++, at, checkId: checked.check_id, action: checked.action, reason: checked.reason };
    setLog((entries) => [entry, ...entries].slice(0, 40));
  }

  /** Called by the watcher when the scene has settled and changed: check it without freezing the video. */
  async function autoCheckNow() {
    if (autoCheckingRef.current) return;
    autoCheckingRef.current = true;
    setAutoChecking(true);
    setError(null);
    setNotice(null);
    const at = source.timeLabel();
    if (source.kind === "video") source.pause(); // a recording waits for the AI so no step is skipped
    let resumeAfterMs = 0;
    try {
      const frame = await source.captureFrame();
      if (!frame) throw new Error("Could not read a frame from the video.");
      const response = await api.checkPhoto(unit.unit_id, frame, "camera_capture.jpg");
      onUnitChange(response.unit);
      setLiveResult(response.result);
      addToLog(at, response.result);
      resumeAfterMs = response.result.action === "pass" ? VIDEO_PAUSE_AFTER_PASS_MS : VIDEO_PAUSE_AFTER_PROBLEM_MS;
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      autoCheckingRef.current = false;
      setAutoChecking(false);
      if (source.kind === "video") window.setTimeout(source.resume, resumeAfterMs);
    }
  }

  function backToCamera() {
    setPhase("live");
    setResult(null);
    setFrozenUrl(null);
  }

  /** Manual check (button or uploaded photo): freeze the photo on screen until the worker continues. */
  async function checkPhoto(photo: Blob, fileName: string) {
    setError(null);
    setNotice(null);
    setLiveResult(null);
    const at = source.timeLabel();
    if (source.kind === "video") source.pause();
    setFrozenUrl(URL.createObjectURL(photo));
    setPhase("checking");
    try {
      const response = await api.checkPhoto(unit.unit_id, photo, fileName);
      onUnitChange(response.unit);
      setResult(response.result);
      addToLog(at, response.result);
      setPhase("result");
    } catch (e) {
      setError(errorMessage(e));
      backToCamera();
    }
  }

  async function captureAndCheck() {
    const frame = await source.captureFrame();
    if (frame) await checkPhoto(frame, "camera_capture.jpg");
    else setError("The camera or video isn't ready. Wait a moment, or upload a photo.");
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
      setLiveResult(null);
      backToCamera();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  if (!current) return null; // the unit is complete; App shows the completion screen

  // Keep the camera area while a photo is checked or its result is shown,
  // even if the unit has already advanced to a manual or gate step.
  const showCamera = current.kind === "visual" || phase !== "live" || liveResult !== null || autoChecking;
  const canCapture = ["live", "playing", "paused", "ended"].includes(source.status);

  return (
    <main className="station">
      <StepList steps={unit.steps} />

      <section className="workspace">
        {error && <p className="error banner">{error}</p>}
        {notice && phase === "live" && !liveResult && <p className="notice banner">{notice}</p>}

        {/* Hidden (not removed) during manual and gate steps, so the camera or recorded video keeps running. */}
        <div className={showCamera ? "camera-block" : "camera-block is-hidden"}>
            {current.hides && phase === "live" && !liveResult && (
              <p className="notice banner">🔓 This step covers earlier work. Unlocked because all its checks passed.</p>
            )}
            <SourceControls source={source} autoCheck={autoCheck} onToggleAuto={setAutoCheck} />
            <CaptureStage
              phase={phase}
              videoRef={source.videoRef}
              sourceKind={source.kind}
              sourceStatus={source.status}
              sourceMessage={source.message}
              frozenUrl={frozenUrl}
              result={result}
              liveResult={liveResult}
              autoCheck={autoCheck}
              autoChecking={autoChecking}
              watcher={watcher}
              elapsedSeconds={elapsedSeconds}
              modelName={modelName}
            />

            {phase === "result" && result ? (
              <ResultCard result={result} onRetake={backToCamera} onContinue={backToCamera} onOverride={() => setOverrideOpen(true)} />
            ) : (
              <div className="capture-actions">
                <button
                  className="button button-primary button-large"
                  disabled={phase === "checking" || autoChecking || !canCapture || current.kind !== "visual"}
                  onClick={captureAndCheck}
                >
                  {phase === "checking" ? "Checking…" : autoCheck ? "Check now" : "Check"}
                </button>
                <button
                  className="button button-ghost"
                  disabled={phase === "checking" || autoChecking || current.kind !== "visual"}
                  onClick={() => uploadInput.current?.click()}
                >
                  Upload photo
                </button>
                {liveResult && liveResult.action !== "pass" && (
                  <button className="button button-ghost" onClick={() => setOverrideOpen(true)}>
                    Override…
                  </button>
                )}
                <input ref={uploadInput} type="file" accept="image/jpeg,image/png" hidden onChange={uploadAndCheck} />
              </div>
            )}
        </div>

        {!showCamera && current.kind === "manual" && (
          <ManualPanel check={current} busy={busy} onConfirm={(ok, note) => runStepAction(() => api.confirmManual(unit.unit_id, ok, note))} />
        )}

        {!showCamera && current.kind === "gate" && (
          <GatePanel check={current} busy={busy} onConfirm={() => runStepAction(() => api.confirmGate(unit.unit_id))} />
        )}

        <CheckLog entries={log} />
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
