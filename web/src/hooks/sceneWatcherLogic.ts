// The watcher's rules, kept free of React and timers so they can be tested with exact times
// (see web/scripts/test-scene-watcher.ts). The hook in useSceneWatcher.ts feeds it samples.
//
// It looks at a tiny grey copy of the video and only asks the AI when the scene has settled
// AND looks different from the last check. That keeps checks accurate (no moving hands) and
// under the team's shared rate limit. Tune these after trying a real camera over the real box.

export const WATCHER = {
  sampleWidth: 64,
  sampleHeight: 48,
  sampleEveryMs: 200,
  steadyMs: 1200, // the scene must stay still this long before a check
  newStepGraceMs: 4000, // after a step passes, an unchanged scene is checked for the next step after this
  minGapMs: 2500, // never start two checks closer together than this
  pixelDiff: 22, // brightness difference (0–255) that counts a pixel as "changed"
  movingFraction: 0.02, // >2% of pixels changed since the last sample = something is moving
  changedFraction: 0.04, // >4% changed since the last checked frame = a new scene worth checking
  darkMean: 30, // average brightness below this = too dark to judge
};

export type WatchState = "idle" | "dark" | "moving" | "settling" | "waiting-change" | "ready";

export interface WatchView {
  state: WatchState;
  progress: number; // 0–1 while settling
}

export interface WatchInput {
  enabled: boolean;
  busy: boolean; // a check is running; never start another
  stepKey: string; // the current check id
  sample: Uint8Array | null; // tiny grey frame, or null when no frame is available right now
  now: number; // milliseconds
}

/** What the watcher remembers between samples. */
export interface WatchMemory {
  previous: Uint8Array | null;
  lastChecked: Uint8Array | null;
  lastCheckedStep: string;
  steadySince: number;
  lastTriggerAt: number;
  stepKey: string;
  stepChangedAt: number;
}

export function newWatchMemory(): WatchMemory {
  return {
    previous: null,
    lastChecked: null,
    lastCheckedStep: "",
    steadySince: 0,
    lastTriggerAt: Number.NEGATIVE_INFINITY,
    stepKey: "",
    stepChangedAt: 0,
  };
}

/**
 * One sample in, one decision out. Returns null when there is no frame to judge
 * (keep showing what was shown before), otherwise what to show and whether to check now.
 */
export function watchStep(m: WatchMemory, input: WatchInput): (WatchView & { trigger: boolean }) | null {
  const { enabled, busy, stepKey, sample, now } = input;
  const view = (state: WatchState, progress = 0, trigger = false) => ({ state, progress, trigger });

  if (stepKey !== m.stepKey) {
    m.stepKey = stepKey;
    m.stepChangedAt = now;
  }
  if (!enabled) {
    m.previous = null;
    m.steadySince = 0;
    return view("idle");
  }
  if (sample === null) return null; // buffering or seeking: skip this sample, keep counting

  if (average(sample) < WATCHER.darkMean) {
    m.previous = sample;
    m.steadySince = 0;
    return view("dark");
  }

  const moving = m.previous !== null && changedFraction(sample, m.previous) > WATCHER.movingFraction;
  m.previous = sample;
  if (moving) {
    m.steadySince = 0;
    return view("moving");
  }

  m.steadySince ||= now;
  const progress = Math.min(1, (now - m.steadySince) / WATCHER.steadyMs);
  if (progress < 1) return view("settling", progress);
  if (busy) return view("ready", 1);

  const sceneChanged = m.lastChecked === null || changedFraction(sample, m.lastChecked) > WATCHER.changedFraction;
  const newStepWaitedLongEnough = m.lastCheckedStep !== stepKey && now - m.stepChangedAt >= WATCHER.newStepGraceMs;
  if (!sceneChanged && !newStepWaitedLongEnough) return view("waiting-change", 1);
  if (now - m.lastTriggerAt < WATCHER.minGapMs) return view("ready", 1);

  m.lastChecked = sample;
  m.lastCheckedStep = stepKey;
  m.lastTriggerAt = now;
  return view("ready", 1, true);
}

export function average(gray: Uint8Array): number {
  let sum = 0;
  for (const value of gray) sum += value;
  return sum / gray.length;
}

/** Share of pixels whose brightness differs by more than WATCHER.pixelDiff between two samples. */
export function changedFraction(a: Uint8Array, b: Uint8Array): number {
  let changed = 0;
  for (let i = 0; i < a.length; i++) {
    if (Math.abs(a[i] - b[i]) > WATCHER.pixelDiff) changed++;
  }
  return changed / a.length;
}
