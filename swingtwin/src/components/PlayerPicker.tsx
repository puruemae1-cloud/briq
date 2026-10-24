import { useMemo, useState } from "react";
import { IG_SOURCES, PROS, searchPros } from "@/lib/players";
import type { ProProfile } from "@/lib/types";

export function PlayerPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (id: string) => void;
}) {
  const [q, setQ] = useState("");
  const [source, setSource] = useState<string>("all");
  const list = useMemo(() => {
    const base = searchPros(q);
    if (source === "all") return base;
    return base.filter((p) => p.sources?.includes(source));
  }, [q, source]);
  const selected: ProProfile | undefined = PROS.find((p) => p.id === value);

  return (
    <div className="twin-picker">
      <label>
        Player
        <input
          type="search"
          placeholder="Search 100 PGA names…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </label>
      <label>
        Learned from
        <select value={source} onChange={(e) => setSource(e.target.value)}>
          <option value="all">All five Instagram archives</option>
          {IG_SOURCES.filter((s) => s.id !== "purego1f").map((s) => (
            <option key={s.id} value={s.id}>
              {s.handle}
            </option>
          ))}
        </select>
      </label>
      <select
        size={8}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="PGA player"
      >
        {list.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
            {p.country ? ` · ${p.country}` : ""}
          </option>
        ))}
      </select>
      {selected ? (
        <p className="twin-note">
          {selected.signature} {list.length} players in this filter.
        </p>
      ) : null}
    </div>
  );
}
