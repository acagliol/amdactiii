import type { Action } from "./types";

/** "charger_and_cable_present" -> "Charger and cable present" */
export function readableId(id: string): string {
  const words = id.replace(/[_-]+/g, " ").trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export const ACTION_LABEL: Record<Action, string> = {
  pass: "Pass",
  fix: "Fix it",
  retake: "Retake",
  supervisor: "Supervisor needed",
};

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Try again.";
}

export function formatTime(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  return Number.isNaN(date.getTime()) ? isoTimestamp : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
