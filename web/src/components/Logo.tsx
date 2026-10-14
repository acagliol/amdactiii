// The Multilönd mark: viewfinder brackets + an open ring.
// The ring doubles as the status indicator: it spins while the AI checks,
// closes green on Pass, and turns red / amber on Fix it / Retake.

export type RingState = "idle" | "checking" | "pass" | "fix" | "retake" | "supervisor";

interface LogoMarkProps {
  size?: number;
  state?: RingState;
}

export function LogoMark({ size = 32, state = "idle" }: LogoMarkProps) {
  return (
    <svg className={`logo-mark ring-${state}`} viewBox="0 0 100 100" width={size} height={size} aria-hidden="true">
      <path
        className="logo-brackets"
        d="M12 32V12h20M68 12h20v20M12 68v20h20M88 68v20H68"
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
        strokeLinecap="square"
      />
      <circle className="logo-ring" cx="50" cy="50" r="20" fill="none" strokeWidth="5" pathLength={100} />
    </svg>
  );
}

export function Wordmark({ large = false }: { large?: boolean }) {
  return <span className={large ? "wordmark wordmark-large" : "wordmark"}>MULTILÖND</span>;
}
