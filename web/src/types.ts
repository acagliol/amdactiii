// Shapes returned by the Python API (api/server.py). Keep in sync with unit_state().

export type Action = "pass" | "fix" | "retake" | "supervisor";
export type CheckKind = "visual" | "manual" | "gate";
export type StepStatus = "done" | "overridden" | "current" | "upcoming";

/** [ymin, xmin, ymax, xmax] on a 0–1000 scale of the photo the AI saw. */
export type ProblemBox = [number, number, number, number];

export interface Step {
  check_id: string;
  step_id: string;
  instruction: string;
  kind: CheckKind;
  hides: boolean;
  requires: string[];
  status: StepStatus;
}

export interface GateStatus {
  blocked: boolean;
  missing: string[];
  hides: boolean;
}

export interface CurrentCheck {
  check_id: string;
  step_id: string;
  kind: CheckKind;
  instruction: string;
  question: string;
  show: string | null;
  hides: boolean;
  requires: string[];
  gate: GateStatus;
  reference_url: string | null;
}

export interface UnitState {
  unit_id: string;
  assembly: string;
  assembly_file: string;
  done: number;
  total: number;
  complete: boolean;
  retake_streak: number;
  overrides: { check_id: string; reason: string }[];
  steps: Step[];
  current: CurrentCheck | null;
}

export interface CheckResult {
  action: Action;
  reason: string;
  problem_box: ProblemBox | null;
  hint: string | null;
  step_id: string;
  check_id: string;
  photo_url: string | null;
}

export interface ActionResponse {
  result: CheckResult;
  unit: UnitState;
}

export interface AssemblyInfo {
  file: string;
  name: string;
  checks: number;
}

export interface Health {
  ok: boolean;
  ai: "fake" | "real";
  model: string | null;
}

export interface EvidenceItem {
  unit_id: string;
  step_id: string;
  check_id: string;
  timestamp: string;
  verdict: string | null;
  action: Action;
  reason: string;
  problem_box: ProblemBox | null;
  photo_url: string | null;
}

export interface EvidenceResponse {
  summary: { attempts: number; units_seen: number; actions: Record<Action, number> };
  items: EvidenceItem[];
}
