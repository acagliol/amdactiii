import { useEffect, useState } from "react";
import { api } from "./api";
import { CompleteScreen } from "./components/CompleteScreen";
import { Header } from "./components/Header";
import { StartScreen } from "./components/StartScreen";
import { Station } from "./components/Station";
import { errorMessage } from "./format";
import type { AssemblyInfo, CustomChecklist, Health, UnitState } from "./types";

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

  /** Start a unit from either option on the start screen, showing any error there. */
  async function start(request: () => Promise<UnitState>) {
    setStarting(true);
    setError(null);
    try {
      setUnit(await request());
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setStarting(false);
    }
  }

  const startUnit = (assemblyFile: string, serial: string) => start(() => api.startUnit(assemblyFile, serial));
  const startCustomUnit = (spec: CustomChecklist, serial: string) => start(() => api.startCustomUnit(spec, serial));

  const modelName = health?.ai === "real" ? `${health.model ?? "the AI"} on AMD` : "the demo AI";

  return (
    <div className="app">
      <Header health={health} unit={unit} />
      {!unit && (
        <StartScreen
          assemblies={assemblies}
          busy={starting}
          error={error}
          onStart={startUnit}
          onStartCustom={startCustomUnit}
        />
      )}
      {unit && !unit.complete && <Station unit={unit} modelName={modelName} onUnitChange={setUnit} />}
      {unit && unit.complete && <CompleteScreen unit={unit} onNextUnit={() => setUnit(null)} />}
    </div>
  );
}
