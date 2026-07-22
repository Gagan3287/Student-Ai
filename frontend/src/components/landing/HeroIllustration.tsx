/**
 * HeroIllustration — self-contained inline SVG.
 * No external image, no npm illustration library required.
 * Palette: indigo/violet matching the StudyMate brand.
 */
export default function HeroIllustration({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 420 340"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Background glow blobs */}
      <ellipse cx="210" cy="290" rx="170" ry="32" fill="url(#shadowGrad)" opacity="0.18" />
      <circle cx="320" cy="80" r="70" fill="url(#blobRight)" opacity="0.12" />
      <circle cx="90" cy="120" r="55" fill="url(#blobLeft)" opacity="0.10" />

      {/* Desk */}
      <rect x="50" y="240" width="320" height="16" rx="8" fill="url(#deskGrad)" />
      <rect x="90" y="255" width="14" height="50" rx="7" fill="#6366f1" opacity="0.3" />
      <rect x="316" y="255" width="14" height="50" rx="7" fill="#6366f1" opacity="0.3" />

      {/* Laptop base */}
      <rect x="120" y="200" width="180" height="10" rx="5" fill="#4f46e5" />
      <rect x="115" y="208" width="190" height="6" rx="3" fill="#4338ca" opacity="0.5" />

      {/* Laptop screen */}
      <rect x="130" y="120" width="160" height="85" rx="8" fill="#1e1b4b" />
      <rect x="134" y="124" width="152" height="77" rx="6" fill="#312e81" />
      {/* Screen glow lines */}
      <rect x="142" y="134" width="90" height="5" rx="2.5" fill="#818cf8" opacity="0.7" />
      <rect x="142" y="146" width="120" height="4" rx="2" fill="#6366f1" opacity="0.5" />
      <rect x="142" y="156" width="100" height="4" rx="2" fill="#6366f1" opacity="0.4" />
      <rect x="142" y="166" width="80" height="4" rx="2" fill="#6366f1" opacity="0.3" />
      <rect x="142" y="176" width="110" height="4" rx="2" fill="#6366f1" opacity="0.25" />
      {/* Cursor blink */}
      <rect x="260" y="134" width="3" height="10" rx="1.5" fill="#a5b4fc" opacity="0.9" />

      {/* Student body */}
      {/* Chair back */}
      <rect x="175" y="205" width="70" height="6" rx="3" fill="#6366f1" opacity="0.4" />
      {/* Torso */}
      <rect x="185" y="211" width="50" height="32" rx="10" fill="url(#torsoGrad)" />
      {/* Arms */}
      <path d="M 185 225 Q 155 235 148 242" stroke="#a78bfa" strokeWidth="10" strokeLinecap="round" />
      <path d="M 235 225 Q 265 235 272 242" stroke="#a78bfa" strokeWidth="10" strokeLinecap="round" />
      {/* Hands on desk area */}
      <circle cx="148" cy="244" r="8" fill="#c4b5fd" />
      <circle cx="272" cy="244" r="8" fill="#c4b5fd" />

      {/* Head */}
      <circle cx="210" cy="195" r="26" fill="url(#skinGrad)" />
      {/* Hair */}
      <ellipse cx="210" cy="176" rx="20" ry="13" fill="#1e1b4b" />
      <ellipse cx="196" cy="184" rx="8" ry="10" fill="#1e1b4b" />
      <ellipse cx="224" cy="184" rx="8" ry="10" fill="#1e1b4b" />
      {/* Eyes */}
      <circle cx="202" cy="196" r="3.5" fill="#1e1b4b" />
      <circle cx="218" cy="196" r="3.5" fill="#1e1b4b" />
      <circle cx="203.5" cy="194.5" r="1" fill="white" />
      <circle cx="219.5" cy="194.5" r="1" fill="white" />
      {/* Glasses */}
      <rect x="196" y="192" width="11" height="8" rx="3" stroke="#818cf8" strokeWidth="1.5" fill="none" />
      <rect x="213" y="192" width="11" height="8" rx="3" stroke="#818cf8" strokeWidth="1.5" fill="none" />
      <line x1="207" y1="196" x2="213" y2="196" stroke="#818cf8" strokeWidth="1.5" />
      {/* Smile */}
      <path d="M 204 205 Q 210 210 216 205" stroke="#7c6f5e" strokeWidth="1.5" strokeLinecap="round" fill="none" />

      {/* Books stack on right */}
      <rect x="295" y="218" width="52" height="12" rx="4" fill="#4f46e5" />
      <rect x="300" y="207" width="44" height="12" rx="4" fill="#7c3aed" />
      <rect x="297" y="196" width="48" height="12" rx="4" fill="#6366f1" />
      {/* Book spines */}
      <line x1="299" y1="196" x2="299" y2="208" stroke="white" strokeWidth="1" opacity="0.3" />
      <line x1="302" y1="207" x2="302" y2="219" stroke="white" strokeWidth="1" opacity="0.3" />
      <line x1="297" y1="218" x2="297" y2="230" stroke="white" strokeWidth="1" opacity="0.3" />

      {/* Notebook on left */}
      <rect x="72" y="210" width="55" height="32" rx="5" fill="#e0e7ff" />
      <rect x="72" y="210" width="7" height="32" rx="3.5" fill="#6366f1" />
      <line x1="84" y1="220" x2="120" y2="220" stroke="#c7d2fe" strokeWidth="1.5" />
      <line x1="84" y1="228" x2="120" y2="228" stroke="#c7d2fe" strokeWidth="1.5" />
      <line x1="84" y1="236" x2="110" y2="236" stroke="#c7d2fe" strokeWidth="1.5" />

      {/* Floating sparkles */}
      <g opacity="0.75">
        <path d="M 340 55 L 342 48 L 344 55 L 351 57 L 344 59 L 342 66 L 340 59 L 333 57 Z" fill="#a5b4fc" />
        <path d="M 68 75 L 70 69 L 72 75 L 78 77 L 72 79 L 70 85 L 68 79 L 62 77 Z" fill="#c4b5fd" />
        <circle cx="365" cy="140" r="4" fill="#818cf8" opacity="0.5" />
        <circle cx="55" cy="160" r="3" fill="#a78bfa" opacity="0.5" />
        <circle cx="355" cy="180" r="2.5" fill="#c4b5fd" opacity="0.6" />
        <circle cx="75" cy="230" r="2" fill="#818cf8" opacity="0.4" />
      </g>

      {/* Floating AI chip icon top right */}
      <rect x="348" y="100" width="36" height="36" rx="8" fill="url(#chipGrad)" opacity="0.85" />
      <rect x="355" y="107" width="22" height="22" rx="4" fill="#1e1b4b" opacity="0.5" />
      <rect x="360" y="112" width="12" height="12" rx="2" fill="#818cf8" opacity="0.9" />
      <line x1="348" y1="112" x2="355" y2="112" stroke="#6366f1" strokeWidth="1.5" />
      <line x1="348" y1="118" x2="355" y2="118" stroke="#6366f1" strokeWidth="1.5" />
      <line x1="348" y1="124" x2="355" y2="124" stroke="#6366f1" strokeWidth="1.5" />
      <line x1="377" y1="112" x2="384" y2="112" stroke="#6366f1" strokeWidth="1.5" />
      <line x1="377" y1="118" x2="384" y2="118" stroke="#6366f1" strokeWidth="1.5" />
      <line x1="377" y1="124" x2="384" y2="124" stroke="#6366f1" strokeWidth="1.5" />

      {/* Defs */}
      <defs>
        <linearGradient id="deskGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#4338ca" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>
        <linearGradient id="torsoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>
        <linearGradient id="skinGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#fde68a" />
          <stop offset="100%" stopColor="#fbbf24" />
        </linearGradient>
        <linearGradient id="blobRight" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#818cf8" />
          <stop offset="100%" stopColor="#a78bfa" />
        </linearGradient>
        <linearGradient id="blobLeft" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#c4b5fd" />
          <stop offset="100%" stopColor="#818cf8" />
        </linearGradient>
        <radialGradient id="shadowGrad">
          <stop offset="0%" stopColor="#4f46e5" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
        <linearGradient id="chipGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>
    </svg>
  );
}
