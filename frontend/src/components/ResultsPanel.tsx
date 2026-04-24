import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  ClipboardList,
  LineChart,
  Sparkles,
} from "lucide-react";
import type { ScoreResponse, Subscores } from "@/types";

const SUB_LABELS: Record<keyof Subscores, string> = {
  format_and_structure: "Format & structure",
  semantic_fit_vs_job_description: "Semantic fit vs. job description",
  keyword_coverage_vs_job_description: "Keyword coverage vs. job description",
};

function clamp(n: number) {
  if (!Number.isFinite(n)) return 0;
  return Math.min(100, Math.max(0, n));
}

function ScoreRing({ score }: { score: number }) {
  const r = 38;
  const c = 2 * Math.PI * r;
  const p = clamp(score) / 100;

  return (
    <div className="relative mx-auto h-36 w-36">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 88 88" aria-hidden>
        <defs>
          <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#43b047" />
            <stop offset="100%" stopColor="#f4b000" />
          </linearGradient>
        </defs>
        <circle cx="44" cy="44" r={r} fill="none" stroke="rgba(0,0,0,0.10)" strokeWidth="8" className="dark:[stroke:rgba(255,255,255,0.08)]" />
        <motion.circle
          cx="44"
          cy="44"
          r={r}
          fill="none"
          stroke="url(#scoreGrad)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - p) }}
          transition={{ duration: 1.05, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          key={score}
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-3xl font-bold tabular-nums tracking-tight text-ink-950 dark:text-white"
        >
          {Math.round(score)}
        </motion.span>
        <span className="text-[11px] font-semibold uppercase tracking-widest text-ink-600 dark:text-ink-500">/ 100</span>
      </div>
    </div>
  );
}

function SubscoreRow({ label, value }: { label: string; value: number | undefined }) {
  const n = value === undefined ? NaN : Number(value);
  const pct = Number.isFinite(n) ? clamp(n) : 0;
  const display = value === undefined ? "—" : String(value);

  return (
    <div className="rounded-2xl border border-black/10 bg-white/65 p-4 transition-colors dark:border-white/10 dark:bg-ink-950/50">
      <div className="mb-2 flex items-start justify-between gap-3">
        <p className="text-sm leading-snug text-ink-700 dark:text-ink-300">{label}</p>
        <span className="shrink-0 text-sm font-bold tabular-nums text-ink-950 dark:text-white">{display}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
        <motion.div
          className="h-full rounded-full bg-brand-navy dark:bg-white"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.85, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
    </div>
  );
}

type Props = {
  result: ScoreResponse | null;
  error: string | null;
  loading: boolean;
  onViewDetails?: () => void;
  onOpenSnippet?: (url: string) => void;
};

export function ResultsPanel({ result, error, loading, onViewDetails, onOpenSnippet }: Props) {
  const sub = result?.subscores;

  const empty = !loading && !result && !error;

  return (
    <motion.section
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.06, ease: [0.22, 1, 0.36, 1] }}
      className="h-full"
    >
      <div className="h-full rounded-3xl bg-gradient-to-b from-black/10 to-black/0 p-[1px] dark:from-white/12 dark:to-white/0">
        <div className="relative flex h-full flex-col overflow-hidden rounded-3xl bg-white/70 p-5 shadow-card-light backdrop-blur-xl transition-colors md:p-6 dark:bg-white/[0.035] dark:shadow-card">
          <div className="pointer-events-none absolute -left-20 bottom-0 h-56 w-56 rounded-full bg-black/[0.05] blur-3xl dark:bg-white/[0.05]" />

      <header className="relative mb-6 border-b border-black/10 pb-4 dark:border-white/10">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-700 dark:text-ink-300">Insights</p>
        <h2 className="mt-1 flex items-center gap-2 text-2xl font-semibold tracking-tight text-ink-950 dark:text-white">
          <LineChart className="h-7 w-7 text-ink-950 dark:text-white" aria-hidden />
          Results
        </h2>
        <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">Overall score and the three subscores. Open details for full feedback.</p>
      </header>

      <AnimatePresence mode="wait">
        {empty && (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="relative flex flex-1 flex-col items-center justify-center py-10 text-center"
          >
            <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-black/10 bg-black/[0.03] dark:border-white/10 dark:bg-white/5">
              <Sparkles className="h-8 w-8 text-ink-950 dark:text-white" />
            </div>
            <p className="max-w-xs text-sm leading-relaxed text-ink-600 dark:text-ink-400">
              Your scores will appear here after you run an analysis.
            </p>
          </motion.div>
        )}

        {loading && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 space-y-5 py-2"
          >
            <div className="mx-auto h-36 w-36 animate-pulse rounded-full bg-black/10 dark:bg-white/10" />
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 animate-pulse rounded-2xl bg-black/[0.03] dark:bg-white/5" />
              ))}
            </div>
          </motion.div>
        )}

        {error && !loading && (
          <motion.div
            key="error"
            role="alert"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900 dark:border-rose-500/35 dark:bg-rose-500/10 dark:text-rose-50"
          >
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-700 dark:text-rose-200" aria-hidden />
            <p className="leading-relaxed">{error}</p>
          </motion.div>
        )}

        {result && !loading && (
          <motion.div
            key="data"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="relative flex-1 space-y-6"
          >
            <div className="flex flex-col items-center gap-2 border-b border-white/10 pb-8">
              <ScoreRing score={result.overall_score ?? 0} />
              <p className="text-center text-xs font-medium uppercase tracking-[0.2em] text-ink-600 dark:text-ink-500">Overall score</p>
              {result.filename && (
                <p className="text-center text-xs text-ink-600 dark:text-ink-500">
                  File: <span className="text-ink-800 dark:text-ink-300">{result.filename}</span>
                </p>
              )}
            </div>

            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-ink-600 dark:text-ink-500">
                <ClipboardList className="h-4 w-4" aria-hidden />
                Subscores
              </h3>
              {(Object.keys(SUB_LABELS) as (keyof Subscores)[]).map((key) => (
                <SubscoreRow key={key} label={SUB_LABELS[key]} value={sub?.[key]} />
              ))}
            </div>

            <div className="flex flex-col items-center justify-center gap-2 sm:flex-row">
              <button
                type="button"
                onClick={onViewDetails}
                className="rounded-xl border border-black/10 bg-white/70 px-4 py-2 text-sm font-semibold text-ink-900 shadow-sm transition hover:bg-white dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-100 dark:hover:bg-white/[0.09]"
              >
                View full feedback
              </button>
              {onOpenSnippet &&
                (() => {
                  const relAnn = result.annotated_document_preview?.url?.trim();
                  const rel0 = result.weak_section_snippet?.url?.trim();
                  const plan = result.improvement_plan ?? [];
                  const hit = plan.find((p) => p?.snippet_image_url);
                  const rel = relAnn || rel0 || hit?.snippet_image_url?.trim();
                  if (!rel) return null;
                  return (
                    <button
                      type="button"
                      onClick={() => onOpenSnippet(rel)}
                      className="rounded-xl border border-black/10 bg-white/70 px-4 py-2 text-sm font-semibold text-ink-900 shadow-sm transition hover:bg-white dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-100 dark:hover:bg-white/[0.09]"
                    >
                      {relAnn ? "Preview document (issues marked)" : "Preview weak section"}
                    </button>
                  );
                })()}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
        </div>
      </div>
    </motion.section>
  );
}
