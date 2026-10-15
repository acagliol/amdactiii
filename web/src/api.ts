// Small typed wrapper around the Python API. Every call returns parsed JSON or throws
// an Error whose message is safe to show to the worker.
import type { ActionResponse, AssemblyInfo, EvidenceResponse, Health, UnitState } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new Error("Cannot reach the station server. Is it running?");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${response.status}).`;
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

function postJson(body: unknown): RequestInit {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

const unitPath = (unitId: string) => `/api/units/${encodeURIComponent(unitId)}`;

export const api = {
  health: () => request<Health>("/api/health"),

  assemblies: () => request<AssemblyInfo[]>("/api/assemblies"),

  startUnit: (assembly: string, serial: string) =>
    request<UnitState>("/api/units", postJson({ assembly, serial: serial.trim() || null })),

  checkPhoto: (unitId: string, photo: Blob, fileName: string) => {
    const form = new FormData();
    form.append("photo", photo, fileName);
    return request<ActionResponse>(`${unitPath(unitId)}/check`, { method: "POST", body: form });
  },

  confirmManual: (unitId: string, ok: boolean, note: string) =>
    request<ActionResponse>(`${unitPath(unitId)}/manual`, postJson({ ok, note })),

  confirmGate: (unitId: string) => request<ActionResponse>(`${unitPath(unitId)}/gate`, { method: "POST" }),

  override: (unitId: string, reason: string) =>
    request<ActionResponse>(`${unitPath(unitId)}/override`, postJson({ reason })),

  evidence: (unitId: string) =>
    request<EvidenceResponse>(`/api/evidence?unit_id=${encodeURIComponent(unitId)}&limit=50`),
};
