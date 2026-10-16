// Tests for the watcher's rules with exact times (no browser, no timers).
// Run:  npm run test:watcher   (from web/)
import assert from "node:assert/strict";
import { newWatchMemory, WATCHER, watchStep, type WatchInput, type WatchMemory } from "../src/hooks/sceneWatcherLogic.ts";

const PIXELS = WATCHER.sampleWidth * WATCHER.sampleHeight;
const TICK = WATCHER.sampleEveryMs;

/** An empty box: a flat grey scene, with a little camera noise. */
function emptyBox(noise = 0): Uint8Array {
  return Uint8Array.from({ length: PIXELS }, (_, i) => 120 + ((i * 7) % (noise + 1)));
}

/** The same scene with one item added (a block covering about 13% of the frame). */
function withItem(base: Uint8Array, left = 10): Uint8Array {
  const scene = base.slice();
  for (let y = 10; y < 30; y++) for (let x = left; x < left + 20; x++) scene[y * WATCHER.sampleWidth + x] = 230;
  return scene;
}

/** A hand passing over: a random bright block every frame. */
function handFrame(seed: number): Uint8Array {
  const scene = emptyBox();
  const left = (seed * 13) % 40;
  for (let y = 5; y < 40; y++) for (let x = left; x < left + 24; x++) scene[y * WATCHER.sampleWidth + x] = 200;
  return scene;
}

const dark = () => new Uint8Array(PIXELS).fill(10);

/** Feed one sample per tick for `ms` milliseconds; return what happened. */
function run(m: WatchMemory, clock: { now: number }, ms: number, sample: () => Uint8Array | null, extra: Partial<WatchInput> = {}) {
  const states: string[] = [];
  const triggers: number[] = [];
  for (let elapsed = 0; elapsed < ms; elapsed += TICK) {
    clock.now += TICK;
    const decision = watchStep(m, { enabled: true, busy: false, stepKey: "step-1", sample: sample(), now: clock.now, ...extra });
    if (decision) {
      states.push(decision.state);
      if (decision.trigger) triggers.push(clock.now);
    }
  }
  return { states, triggers, last: states[states.length - 1] };
}

const tests: [string, () => void][] = [
  ["a steady scene is checked once, after it has been still long enough", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    const early = run(m, clock, WATCHER.steadyMs - TICK, () => emptyBox(3));
    assert.equal(early.triggers.length, 0);
    assert.equal(early.last, "settling");
    const later = run(m, clock, 3000, () => emptyBox(3));
    assert.equal(later.triggers.length, 1, "exactly one check");
    assert.equal(later.last, "waiting-change", "then it waits for something to change");
  }],
  ["camera noise alone never counts as a change", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    run(m, clock, 2000, () => emptyBox(3));
    let flip = false;
    const noisy = run(m, clock, 5000, () => emptyBox((flip = !flip) ? 3 : 9));
    assert.equal(noisy.triggers.length, 0);
    assert.ok(!noisy.states.includes("moving"));
  }],
  ["a moving hand is never checked; the settled new scene is", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    run(m, clock, 2000, () => emptyBox()); // first check of the empty box
    let seed = 0;
    const hand = run(m, clock, 1500, () => handFrame(seed++));
    assert.equal(hand.triggers.length, 0);
    assert.ok(hand.states.includes("moving"));
    const placed = run(m, clock, 2500, () => withItem(emptyBox()));
    assert.equal(placed.triggers.length, 1, "the new item gets checked");
  }],
  ["after a step passes, an unchanged scene is re-checked only after the grace period", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    run(m, clock, 2000, () => withItem(emptyBox()), { stepKey: "step-1" });
    const soon = run(m, clock, WATCHER.newStepGraceMs - TICK, () => withItem(emptyBox()), { stepKey: "step-2" });
    assert.equal(soon.triggers.length, 0, "no instant re-check: the worker may still be adding the next item");
    const after = run(m, clock, 1000, () => withItem(emptyBox()), { stepKey: "step-2" });
    assert.equal(after.triggers.length, 1, "but if nothing changes, the next step is checked anyway");
  }],
  ["no new check while one is still running", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    const busy = run(m, clock, 3000, () => emptyBox(), { busy: true });
    assert.equal(busy.triggers.length, 0);
    const free = run(m, clock, 400, () => emptyBox());
    assert.equal(free.triggers.length, 1);
  }],
  ["too dark is reported and never checked", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    const result = run(m, clock, 3000, dark);
    assert.equal(result.triggers.length, 0);
    assert.equal(result.last, "dark");
  }],
  ["a missing frame (buffering) does not restart the steady timer", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    let i = 0;
    const result = run(m, clock, WATCHER.steadyMs + 2 * TICK, () => (i++ % 2 ? null : emptyBox()));
    assert.equal(result.triggers.length, 1);
  }],
  ["two checks never start closer together than the minimum gap", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    const first = run(m, clock, 1400, () => emptyBox());
    // A quick change right after a check: it would settle again before the minimum gap is over.
    const second = run(m, clock, 3000, () => withItem(emptyBox(), 30));
    const all = [...first.triggers, ...second.triggers];
    assert.equal(all.length, 2);
    assert.ok(all[1] - all[0] >= WATCHER.minGapMs, `gap was ${all[1] - all[0]} ms`);
  }],
  ["switched off: nothing happens", () => {
    const m = newWatchMemory();
    const clock = { now: 0 };
    const result = run(m, clock, 3000, () => emptyBox(), { enabled: false });
    assert.equal(result.triggers.length, 0);
    assert.equal(result.last, "idle");
  }],
];

let failed = 0;
for (const [name, test] of tests) {
  try {
    test();
    console.log(`✓ ${name}`);
  } catch (error) {
    failed++;
    console.log(`✗ ${name}\n   ${(error as Error).message}`);
  }
}
console.log(failed ? `\n${failed} of ${tests.length} failed` : `\nAll ${tests.length} watcher tests passed`);
process.exit(failed ? 1 : 0);
