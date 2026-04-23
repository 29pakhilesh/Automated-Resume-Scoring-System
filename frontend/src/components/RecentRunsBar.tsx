import { motion } from "framer-motion";
import { History } from "lucide-react";
import type { RunItem } from "@/types";

type Props = {
  runs: RunItem[];
};

function formatWhen(iso: string | null) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(d);
  } catch {
    return "";
  }
}

export function RecentRunsBar({ runs }: Props) {
  if (!runs.length) return null;

  return (
    <section className="mb-10">
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-ink-500 dark:text-ink-400">
        <History className="h-3.5 w-3.5 text-ink-500" aria-hidden />
        Recent runs
      </div>
      <div className="no-scrollbar flex gap-3 overflow-x-auto pb-1">
        {runs.map((r, i) => (
          <motion.div
            key={r.id}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03 }}
            whileHover={{ y: -2 }}
            className="min-w-[200px] shrink-0 rounded-2xl border border-black/10 bg-black/[0.03] p-3 shadow-sm backdrop-blur-md transition-colors hover:border-accent/30 hover:bg-accent/5 dark:border-white/10 dark:bg-white/[0.03]"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="line-clamp-2 text-sm font-medium text-ink-950 dark:text-ink-100">{r.position_title}</p>
              <span className="shrink-0 rounded-lg bg-accent/15 px-2 py-0.5 text-xs font-bold tabular-nums text-accent">
                {Math.round(r.overall_score)}
              </span>
            </div>
            <p className="mt-1 truncate text-xs text-ink-600 dark:text-ink-500">
              {r.filename?.trim() ? r.filename : "Resume"}
            </p>
            <p className="mt-1 text-[10px] uppercase tracking-wider text-ink-500/80 dark:text-ink-600">{formatWhen(r.created_at)}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
