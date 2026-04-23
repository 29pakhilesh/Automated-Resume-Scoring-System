type Props = {
  className?: string;
};

export function LogoMark({ className }: Props) {
  return (
    <svg viewBox="0 0 48 48" className={className} fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <defs>
        <linearGradient id="gRing" x1="14" y1="18" x2="42" y2="38" gradientUnits="userSpaceOnUse">
          <stop stopColor="#43b047" />
          <stop offset="1" stopColor="#f4b000" />
        </linearGradient>
        <linearGradient id="gDoc" x1="10" y1="10" x2="28" y2="36" gradientUnits="userSpaceOnUse">
          <stop stopColor="#273454" />
          <stop offset="1" stopColor="#1f2a44" />
        </linearGradient>
      </defs>

      {/* Document */} 
      <path
        d="M12 10.5c0-1.93 1.57-3.5 3.5-3.5H28c.93 0 1.82.37 2.48 1.03l5.5 5.5c.66.66 1.03 1.55 1.03 2.48V34c0 1.93-1.57 3.5-3.5 3.5H15.5C13.57 37.5 12 35.93 12 34V10.5Z"
        stroke="rgba(255,255,255,0.95)"
        strokeWidth="1.7"
        opacity="0.9"
      />
      <path
        d="M13.2 11.2c0-1.6 1.3-2.9 2.9-2.9H28c.75 0 1.47.3 2 .83l5.2 5.2c.53.53.83 1.25.83 2V34c0 1.6-1.3 2.9-2.9 2.9H16.1c-1.6 0-2.9-1.3-2.9-2.9V11.2Z"
        fill="url(#gDoc)"
        opacity="0.95"
      />
      <path d="M29.7 8.8v5.8c0 .83.67 1.5 1.5 1.5H37" stroke="rgba(255,255,255,0.85)" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="19" cy="18" r="3.2" fill="rgba(255,255,255,0.92)" opacity="0.9" />
      <path d="M14.9 26.6c1.2-2.8 2.7-4.2 4.4-4.2s3.2 1.4 4.4 4.2" stroke="rgba(255,255,255,0.92)" strokeWidth="2.1" strokeLinecap="round" />
      <path d="M26.2 19.1h7.4M26.2 23.1h6.2M16 30.7h17.6" stroke="rgba(255,255,255,0.5)" strokeWidth="1.9" strokeLinecap="round" />

      {/* Score ring */} 
      <circle cx="34.5" cy="29.5" r="8.6" stroke="rgba(255,255,255,0.35)" strokeWidth="2.2" />
      <path
        d="M34.5 20.9a8.6 8.6 0 0 1 7.9 5.2"
        stroke="url(#gRing)"
        strokeWidth="2.6"
        strokeLinecap="round"
      />
      <path
        d="M42.4 26.1a8.6 8.6 0 0 1-3.1 10.6"
        stroke="url(#gRing)"
        strokeWidth="2.6"
        strokeLinecap="round"
      />
      <path d="M31.2 30.1l2.0 2.0 4.2-4.2" stroke="#43b047" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

