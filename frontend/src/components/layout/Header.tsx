interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 flex items-center h-14 px-6 lg:px-8 bg-surface-dim/85 backdrop-blur-xl border-b border-outline-variant/10 transition-all duration-200">
      <div className="flex items-center gap-3 min-w-0">
        <h2 className="font-headline font-semibold text-[15px] text-on-surface leading-none truncate">
          {title}
        </h2>
        <span className="h-3.5 w-px bg-outline-variant/30 flex-shrink-0" />
        <span className="font-label text-[10px] uppercase tracking-widest text-outline px-2 py-1 rounded-md bg-surface-container-high/40 border border-outline-variant/15 flex-shrink-0">
          NODE‑01
        </span>
      </div>
    </header>
  );
}
