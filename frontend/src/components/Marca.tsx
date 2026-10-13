/** Marca de SUSI: cuatro barras que suben, una por cada estado de madurez de una práctica. Pensada para fondos oscuros. */
export default function Marca({ tamano = 28 }: { tamano?: number }) {
  return (
    <svg width={tamano} height={tamano} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <rect x="2.5" y="21" width="5.5" height="8" rx="1.5" fill="var(--d1)" />
      <rect x="10" y="15" width="5.5" height="14" rx="1.5" fill="var(--d2)" />
      <rect x="17.5" y="9" width="5.5" height="20" rx="1.5" fill="var(--d3)" />
      <rect x="25" y="3" width="5.5" height="26" rx="1.5" fill="var(--d4)" />
    </svg>
  );
}
