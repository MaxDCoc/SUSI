import type { ReactNode } from "react";

// Íconos de trazo para la navegación. Son decorativos: el enlace ya tiene su nombre en texto.
function Icono({ children }: { children: ReactNode }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

export const IconoPracticas = () => (
  <Icono>
    <path d="M9 4h6a1 1 0 0 1 1 1v1H8V5a1 1 0 0 1 1-1Z" />
    <path d="M8 6H6a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-2" />
    <path d="M9 12h6M9 16h4" />
  </Icono>
);

export const IconoValidaciones = () => (
  <Icono>
    <circle cx="12" cy="12" r="9" />
    <path d="m8.5 12.5 2.5 2.5 4.5-5" />
  </Icono>
);

export const IconoTablero = () => (
  <Icono>
    <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
  </Icono>
);

export const IconoGreen = () => (
  <Icono>
    <path d="M5 19c0-8 5-14 15-14 0 10-6 15-14 15" />
    <path d="M5 19c2-4 5-7 9-9" />
  </Icono>
);
