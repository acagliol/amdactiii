import { LogoMark } from "../Logo";

/**
 * The product in one picture: an accessory box seen through the camera's viewfinder.
 * The screw bag is missing, so the AI marks the empty spot before the manual covers it.
 */
export function HeroIllustration() {
  return (
    <figure className="hero-visual" aria-label="Camera view of an accessory box with a missing screw bag highlighted in red">
      <svg viewBox="0 0 520 380" role="img" aria-hidden="true">
        {/* viewfinder brackets (same shape as the logo) */}
        <path
          d="M60 74V40h34M426 40h34v34M60 306v34h34M460 306v34h-34"
          fill="none"
          stroke="var(--paper)"
          strokeWidth="4"
          strokeLinecap="square"
        />

        {/* the open box */}
        <rect x="110" y="70" width="300" height="240" rx="12" fill="#16181c" stroke="#3a3e46" strokeWidth="2" />

        {/* charger */}
        <rect x="136" y="96" width="112" height="84" rx="14" fill="#2b2e35" stroke="#454a53" />
        <rect x="170" y="84" width="10" height="16" rx="2" fill="#8d929b" />
        <rect x="204" y="84" width="10" height="16" rx="2" fill="#8d929b" />

        {/* coiled USB cable */}
        <g fill="none" stroke="#e9e9e6" strokeWidth="5">
          <circle cx="330" cy="138" r="40" />
          <circle cx="330" cy="138" r="29" />
          <circle cx="330" cy="138" r="18" />
        </g>

        {/* empty slot where the screw bag should be */}
        <rect x="136" y="206" width="112" height="80" rx="10" fill="none" stroke="#5a5f68" strokeWidth="2" strokeDasharray="7 6" />

        {/* the AI's red box on the problem */}
        <rect className="hero-problem-box" x="126" y="196" width="132" height="100" rx="6" fill="none" stroke="var(--fix)" strokeWidth="4" />

        {/* folded manual: the next step lays it on top, hiding everything below */}
        <g transform="translate(286 214) rotate(-6)">
          <rect width="96" height="70" rx="4" fill="#f3f3f1" />
          <path d="M14 18h68M14 32h68M14 46h44" stroke="#b9bcc2" strokeWidth="4" />
        </g>
      </svg>

      <figcaption className="hero-status">
        <LogoMark size={36} state="fix" />
        <span className="badge badge-fix">Fix it</span>
        <span>Screw bag missing. Add it before the manual covers the items.</span>
      </figcaption>
    </figure>
  );
}
