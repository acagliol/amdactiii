import { useEffect, useState } from "react";
import type { AssemblyInfo } from "../types";
import { LogoMark, Wordmark } from "./Logo";

interface StartScreenProps {
  assemblies: AssemblyInfo[];
  busy: boolean;
  error: string | null;
  onStart: (assemblyFile: string, serial: string) => void;
}

const PREFERRED_DEMO = "packing_box.yaml";

export function StartScreen({ assemblies, busy, error, onStart }: StartScreenProps) {
  const [assemblyFile, setAssemblyFile] = useState("");
  const [serial, setSerial] = useState("");

  // Default to the demo checklist once the list arrives.
  useEffect(() => {
    if (assemblyFile || assemblies.length === 0) return;
    const preferred = assemblies.find((item) => item.file === PREFERRED_DEMO) ?? assemblies[0];
    setAssemblyFile(preferred.file);
  }, [assemblies, assemblyFile]);

  return (
    <main className="start">
      <div className="start-brand">
        <LogoMark size={96} />
        <Wordmark large />
        <p className="tagline">Catch it before it&apos;s covered</p>
      </div>

      <form
        className="start-card"
        onSubmit={(event) => {
          event.preventDefault();
          if (assemblyFile) onStart(assemblyFile, serial);
        }}
      >
        <label className="field">
          <span>Assembly</span>
          <select value={assemblyFile} onChange={(event) => setAssemblyFile(event.target.value)}>
            {assemblies.map((item) => (
              <option key={item.file} value={item.file}>
                {item.name} · {item.checks} checks
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Unit serial (optional)</span>
          <input
            value={serial}
            onChange={(event) => setSerial(event.target.value)}
            placeholder="e.g. BOX-1042"
            maxLength={64}
          />
        </label>

        {error && <p className="error">{error}</p>}

        <button className="button button-primary button-large" type="submit" disabled={busy || !assemblyFile}>
          {busy ? "Starting…" : "Start unit"}
        </button>
      </form>
    </main>
  );
}
