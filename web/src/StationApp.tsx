import { useEffect, useState } from "react";
import { api } from "./api";
import { CompleteScreen } from "./components/CompleteScreen";
import { Header } from "./components/Header";
import { StartScreen } from "./components/StartScreen";
import { Station } from "./components/Station";
import { errorMessage } from "./format";
import type { AssemblyInfo, Health, UnitState } from "./types";

/** The worker station: pick an assembly → work through the unit → see the unit's proof. */
export function StationApp() {
  const [health, setHealth] = useState<Health | null>(null);
  const [assemblies, setAssemblies] = useState<AssemblyInfo[]>([]);
  const [unit, setUnit] = useState<UnitState | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch((e) => setError(errorMessage(e)));
    api.assemblies().then(setAssemblies).catch((e) => setError(errorMessage(e)));
  }, []);

  async function startUnit(assemblyFile: string, serial: string) {
    setStarting(true);
    setError(null);
    try {
      setUnit(await api.startUnit(assemblyFile, serial));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setStarting(false);
    }
  }

  const modelName = health?.ai === "real" ? `${health.model ?? "the AI"} on AMD` : "the demo AI";

  return (
    <div className="app">
      <Header health={health} unit={unit} />
      {!unit && <StartScreen assemblies={assemblies} busy={starting} error={error} onStart={startUnit} />}
      {unit && !unit.complete && <Station unit={unit} modelName={modelName} onUnitChange={setUnit} />}
      {unit && unit.complete && <CompleteScreen unit={unit} onNextUnit={() => setUnit(null)} />}
    </div>
  );
}
