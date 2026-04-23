import { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, Copy, Download, Lightbulb, MoveLeft, Search } from "lucide-react";
import clsx from "clsx";
import type { ImprovementItem, ScoreResponse } from "@/types";

const STORAGE_KEY = "rss.lastScoreResponse.v1";

function prettyArea(area: string | undefined) {
  if (!area) return "Area";
  const a = area.trim();
  if (!a) return "Area";

  // Known backend keys → user-facing labels
  if (a === "format_and_structure") return "Format & structure";
  if (a === "semantic_fit_vs_job_description") return "Semantic fit vs. job description";
  if (a === "keyword_coverage_vs_job_description") return "Keyword coverage vs. job description";

  // Generic snake_case → Title Case
  return a
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .split(" ")
    .map((w) => (w.length ? w[0]!.toUpperCase() + w.slice(1) : w))
    .join(" ");
}

function readStored(): ScoreResponse | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ScoreResponse;
  } catch {
    return null;
  }
}

function severityStyles(s: string | undefined) {
  const u = (s ?? "medium").toLowerCase();
  if (u === "high" || u === "critical") return "bg-rose-500/12 text-rose-800 border-rose-500/25 dark:text-rose-200";
  if (u === "low") return "bg-emerald-500/10 text-emerald-800 border-emerald-500/25 dark:text-emerald-200";
  return "bg-amber-500/10 text-amber-900 border-amber-500/25 dark:text-amber-200";
}

function PlanCard({ item }: { item: ImprovementItem }) {
  return (
    <article className="rounded-2xl border border-black/10 bg-white/80 p-4 shadow-sm dark:border-white/10 dark:bg-white/[0.06]">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-semibold tracking-tight text-ink-950 dark:text-ink-100">
          {prettyArea(item.area)}
        </span>
        <span
          className={clsx(
            "rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide",
            severityStyles(item.severity),
          )}
        >
          {item.severity ?? "medium"}
        </span>
      </div>
      <h4 className="text-[11px] font-bold uppercase tracking-wider text-ink-800 dark:text-ink-300">Why</h4>
      <p className="mt-1 text-sm leading-relaxed text-ink-900 dark:text-ink-200">{item.why}</p>
      <h4 className="mt-4 text-[11px] font-bold uppercase tracking-wider text-ink-800 dark:text-ink-300">
        What to change
      </h4>
      <p className="mt-1 text-sm leading-relaxed text-ink-900 dark:text-ink-200">{item.fix}</p>
    </article>
  );
}

export function DetailsPage() {
  const [data, setData] = useState<ScoreResponse | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setData(readStored());
  }, []);

  const improvement = useMemo(() => data?.improvement_plan ?? [], [data?.improvement_plan]);

  const previewText = (data?.extracted_text_preview ?? "").trim();
  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q || q.length < 2) return 0;
    const hay = previewText.toLowerCase();
    let i = 0;
    let n = 0;
    while (true) {
      const at = hay.indexOf(q, i);
      if (at === -1) break;
      n += 1;
      i = at + q.length;
      if (n > 999) break;
    }
    return n;
  }, [previewText, query]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(previewText || "");
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      // ignore
    }
  };

  const handleDownload = () => {
    try {
      const blob = new Blob([previewText || ""], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "extracted-text-preview.txt";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      // ignore
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 pb-20 pt-10 md:px-6">
      <div className="mb-6 flex items-center justify-between gap-3">
        <a
          href="/"
          className="inline-flex items-center gap-2 rounded-xl border border-black/10 bg-white/70 px-4 py-2 text-sm font-semibold text-ink-900 shadow-sm transition hover:bg-white dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-100 dark:hover:bg-white/[0.09]"
        >
          <MoveLeft className="h-4 w-4" aria-hidden />
          Back
        </a>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">Details</p>
      </div>

      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-ink-950 dark:text-white">Feedback & improvements</h1>
        <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">
          A full breakdown of feedback, prioritized improvements, and optional coaching.
        </p>
      </header>

      {!data && (
        <div className="rounded-3xl border border-black/10 bg-white/70 p-6 text-sm text-ink-700 dark:border-white/10 dark:bg-white/[0.05] dark:text-ink-200">
          No recent results found. Run a score first, then open this page again.
        </div>
      )}

      {data && (
        <div className="space-y-10">
          {data.feedback && data.feedback.length > 0 && (
            <section>
              <h2 className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-ink-600 dark:text-ink-500">
                <Lightbulb className="h-4 w-4 text-amber-500" aria-hidden />
                Feedback
              </h2>
              <ul className="space-y-2">
                {data.feedback.map((text, i) => (
                  <li
                    key={i}
                    className="relative rounded-xl border border-black/10 bg-white/80 py-3 pl-10 pr-3 text-sm leading-relaxed text-ink-900 dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-200"
                  >
                    <span className="absolute left-3 top-3.5 h-2 w-2 rounded-full bg-brand-navy dark:bg-white" />
                    {text}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {improvement.length > 0 && (
            <section>
              <h2 className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-ink-600 dark:text-ink-500">
                Improvement focus
              </h2>
              <div className="space-y-3">
                {improvement.map((item, i) => (
                  <PlanCard key={i} item={item} />
                ))}
              </div>
            </section>
          )}

          <section className="rounded-3xl border border-black/10 bg-white/70 shadow-sm dark:border-white/10 dark:bg-white/[0.05]">
            <button
              type="button"
              onClick={() => setPreviewOpen((o) => !o)}
              className="flex w-full items-center justify-between gap-2 px-6 py-4 text-left text-sm font-semibold text-ink-950 dark:text-white"
            >
              Extracted text preview
              <ChevronDown className={clsx("h-4 w-4 shrink-0 text-ink-400 transition", previewOpen && "rotate-180")} />
            </button>
            {previewOpen && (
              <div className="border-t border-black/10 dark:border-white/10">
                <div className="sticky top-0 z-10 bg-white/80 px-6 py-4 backdrop-blur-md dark:bg-black/60">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div className="flex items-center gap-2">
                      <div className="relative w-full md:w-80">
                        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" aria-hidden />
                        <input
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="Search (min 2 chars)"
                          className="w-full rounded-xl border border-black/10 bg-white/80 py-2 pl-9 pr-3 text-sm text-ink-950 outline-none transition focus:border-black/30 focus:ring-4 focus:ring-black/10 dark:border-white/10 dark:bg-white/[0.06] dark:text-white dark:focus:border-white/25 dark:focus:ring-white/10"
                        />
                      </div>
                      <span className="hidden text-xs text-ink-500 dark:text-ink-400 md:inline">
                        {query.trim().length >= 2 ? `${matches} match${matches === 1 ? "" : "es"}` : `${previewText.length} chars`}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleCopy}
                        className="inline-flex items-center gap-2 rounded-xl border border-black/10 bg-white/70 px-3 py-2 text-sm font-semibold text-ink-900 shadow-sm transition hover:bg-white dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-100 dark:hover:bg-white/[0.09]"
                      >
                        {copied ? <Check className="h-4 w-4" aria-hidden /> : <Copy className="h-4 w-4" aria-hidden />}
                        {copied ? "Copied" : "Copy"}
                      </button>
                      <button
                        type="button"
                        onClick={handleDownload}
                        className="inline-flex items-center gap-2 rounded-xl border border-black/10 bg-white/70 px-3 py-2 text-sm font-semibold text-ink-900 shadow-sm transition hover:bg-white dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-100 dark:hover:bg-white/[0.09]"
                      >
                        <Download className="h-4 w-4" aria-hidden />
                        Download
                      </button>
                    </div>
                  </div>
                </div>

                <div className="px-6 pb-6 pt-4">
                  <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap break-words rounded-2xl border border-black/10 bg-white/70 p-4 font-mono text-xs leading-relaxed text-ink-800 shadow-inner dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-200">
                    {previewText || "—"}
                  </pre>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

