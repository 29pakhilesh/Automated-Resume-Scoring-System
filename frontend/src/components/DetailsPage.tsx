import { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, Copy, Download, Info, Lightbulb, MoveLeft, Search } from "lucide-react";
import clsx from "clsx";
import type { ImprovementItem, ScoreResponse } from "@/types";

const STORAGE_KEY = "rss.lastScoreResponse.v3";

function asStr(v: unknown): string | null {
  if (typeof v === "string") return v;
  if (v === null || v === undefined) return null;
  const s = String(v);
  return s ? s : null;
}

function pick<T extends Record<string, unknown>>(obj: unknown, keys: string[]): Record<string, unknown> {
  if (!obj || typeof obj !== "object") return {};
  const o = obj as T;
  const out: Record<string, unknown> = {};
  for (const k of keys) {
    if (k in o) out[k] = o[k];
  }
  return out;
}

function labelize(key: string) {
  return key
    .replace(/_/g, " ")
    .replace(/\b0 100\b/g, "0–100")
    .replace(/\bjd\b/gi, "JD")
    .replace(/\bvs\b/gi, "vs.")
    .replace(/\s+/g, " ")
    .trim();
}

function renderScalar(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return Number.isFinite(v) ? String(v) : "—";
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (typeof v === "string") return v;
  return String(v);
}

function KeyValueList({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">No details available.</p>;
  }
  return (
    <dl className="mt-2 space-y-2 text-sm">
      {entries.map(([k, v]) => {
        if (k === "sections_found" && v && typeof v === "object") {
          const keys = Object.keys(v as Record<string, unknown>);
          return (
            <div key={k} className="rounded-xl border border-black/10 bg-white/80 p-3 dark:border-white/10 dark:bg-white/[0.06]">
              <dt className="text-xs font-bold uppercase tracking-wide text-ink-600 dark:text-ink-400">
                Sections found
              </dt>
              <dd className="mt-2 flex flex-wrap gap-2">
                {keys.length ? (
                  keys.slice(0, 16).map((s) => (
                    <span
                      key={s}
                      className="rounded-full border border-black/10 bg-white/70 px-2.5 py-1 text-[11px] font-semibold text-ink-800 dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-200"
                    >
                      {s.replace(/_/g, " ")}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-ink-600 dark:text-ink-400">—</span>
                )}
              </dd>
            </div>
          );
        }

        return (
          <div key={k} className="flex items-start justify-between gap-4">
            <dt className="text-ink-700 dark:text-ink-300">{labelize(k)}</dt>
            <dd className="font-semibold tabular-nums text-ink-950 dark:text-ink-100">{renderScalar(v)}</dd>
          </div>
        );
      })}
    </dl>
  );
}

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

function PlanCard({
  item,
}: {
  item: ImprovementItem;
}) {
  const snippetMeta = item.snippet;
  const tp = snippetMeta?.text_preview?.trim();

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

      {tp && (
        <div className="mt-4 rounded-2xl border border-black/10 bg-white/70 p-3 dark:border-white/10 dark:bg-white/[0.04]">
          <p className="text-[11px] font-bold uppercase tracking-wider text-ink-700 dark:text-ink-300">
            Where this shows up in your resume (text snippet)
          </p>
          <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-ink-800 dark:text-ink-200">
            {tp}
          </pre>
        </div>
      )}

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
  const [infoOpen, setInfoOpen] = useState<{ format: boolean; semantic: boolean; keywords: boolean }>({
    format: false,
    semantic: false,
    keywords: false,
  });

  useEffect(() => {
    setData(readStored());
  }, []);

  const improvement = useMemo(() => data?.improvement_plan ?? [], [data?.improvement_plan]);

  const weakRegions = useMemo(() => {
    const w = data?.gap_report?.weakest_resume_segments_vs_jd;
    if (!Array.isArray(w)) return [];
    return w.filter(
      (x): x is { offset?: number; cosine?: number; preview?: string } =>
        !!x && typeof x === "object",
    );
  }, [data?.gap_report?.weakest_resume_segments_vs_jd]);

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
          {weakRegions.length > 0 && (
            <section className="rounded-3xl border border-black/10 bg-white/70 p-6 shadow-sm dark:border-white/10 dark:bg-white/[0.05]">
              <h2 className="text-xs font-bold uppercase tracking-[0.14em] text-ink-600 dark:text-ink-500">
                Weak sections (text)
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-ink-600 dark:text-ink-400">
                These are the resume text chunks that matched the job description the least. Rewrite these first.
              </p>
              <ol className="mt-4 space-y-3">
                {weakRegions
                  .filter((seg) => {
                    const p = (seg.preview ?? "").toLowerCase();
                    if (!p) return true;
                    // extra UI safety: hide contact/header-like chunks
                    if (p.includes("@")) return false;
                    if (p.includes("linkedin") || p.includes("github")) return false;
                    return true;
                  })
                  .slice(0, 4)
                  .map((seg, i) => (
                  <li
                    key={i}
                    className="rounded-2xl border border-black/10 bg-white/80 p-4 dark:border-white/10 dark:bg-white/[0.06]"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-ink-950 dark:text-white">Weak chunk {i + 1}</span>
                      {seg.cosine !== undefined ? (
                        <span className="text-xs font-semibold text-ink-600 dark:text-ink-400">
                          similarity {seg.cosine}
                        </span>
                      ) : null}
                    </div>
                    <pre className="mt-2 whitespace-pre-wrap break-words font-mono text-[12px] leading-relaxed text-ink-800 dark:text-ink-200">
                      {(seg.preview ?? "").trim() || "—"}
                    </pre>
                  </li>
                  ))}
              </ol>
            </section>
          )}

          <section className="rounded-3xl border border-black/10 bg-white/70 p-6 shadow-sm dark:border-white/10 dark:bg-white/[0.05]">
            <h2 className="text-xs font-bold uppercase tracking-[0.14em] text-ink-600 dark:text-ink-500">
              Scoring breakdown
            </h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-black/10 bg-white/80 p-4 dark:border-white/10 dark:bg-white/[0.06]">
                <p className="text-xs font-semibold uppercase tracking-wide text-ink-600 dark:text-ink-400">Weights</p>
                <div className="mt-2 space-y-1 text-sm text-ink-900 dark:text-ink-200">
                  <div className="flex items-center justify-between">
                    <span>Format & structure</span>
                    <span className="font-semibold tabular-nums">
                      {data.weights_applied?.format ?? "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Semantic fit</span>
                    <span className="font-semibold tabular-nums">
                      {data.weights_applied?.semantic ?? "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Keyword fit</span>
                    <span className="font-semibold tabular-nums">
                      {data.weights_applied?.keywords ?? "—"}
                    </span>
                  </div>
                </div>
                {data.position_title_considered ? (
                  <p className="mt-3 text-xs text-ink-600 dark:text-ink-400">
                    Position title used:{" "}
                    <span className="font-semibold text-ink-900 dark:text-ink-200">
                      {data.position_title_considered}
                    </span>
                  </p>
                ) : null}
              </div>

              <div className="rounded-2xl border border-black/10 bg-white/80 p-4 dark:border-white/10 dark:bg-white/[0.06]">
                <p className="text-xs font-semibold uppercase tracking-wide text-ink-600 dark:text-ink-400">
                  Keyword coverage
                </p>
                <div className="mt-2 flex items-center justify-between text-sm text-ink-900 dark:text-ink-200">
                  <span>Matched JD terms</span>
                  <span className="font-semibold tabular-nums">
                    {data.details?.keywords && typeof (data.details.keywords as any).matched_term_count === "number"
                      ? (data.details.keywords as any).matched_term_count
                      : data.gap_report?.keyword_stats?.matched_term_count ?? "—"}
                  </span>
                </div>
                <div className="mt-1 flex items-center justify-between text-sm text-ink-900 dark:text-ink-200">
                  <span>JD term count</span>
                  <span className="font-semibold tabular-nums">
                    {data.details?.keywords && typeof (data.details.keywords as any).jd_term_count === "number"
                      ? (data.details.keywords as any).jd_term_count
                      : data.gap_report?.keyword_stats?.jd_term_count ?? "—"}
                  </span>
                </div>
                <p className="mt-3 text-xs text-ink-600 dark:text-ink-400">
                  If this is low, the overall score will be low even with a strong resume—because it’s measuring fit to
                  the specific JD.
                </p>
              </div>
            </div>

            {(data.gap_report?.missing_keywords_from_jd?.length ?? 0) > 0 && (
              <div className="mt-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-ink-600 dark:text-ink-400">
                  Missing JD keywords (top)
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(data.gap_report?.missing_keywords_from_jd ?? []).slice(0, 24).map((k) => (
                    <span
                      key={k}
                      className="rounded-full border border-black/10 bg-white/80 px-3 py-1 text-xs font-semibold text-ink-800 dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-200"
                    >
                      {k}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <details className="mt-5 rounded-2xl border border-black/10 bg-white/80 p-4 dark:border-white/10 dark:bg-white/[0.06]">
              <summary className="cursor-pointer text-sm font-semibold text-ink-900 dark:text-ink-100">
                Show full scoring details (advanced)
              </summary>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                {(() => {
                  const fmt = (data.details as any)?.format ?? {};
                  const sem = (data.details as any)?.semantic ?? {};
                  const kw = (data.details as any)?.keywords ?? {};

                  const fmtPicked = pick(fmt, [
                    "word_count",
                    "section_coverage_score",
                    "sections_found",
                    "lead_name_and_email_score",
                    "technical_skills_rows_score",
                    "projects_layout_score",
                    "section_order_score",
                    "length_vs_reference_score",
                  ]);
                  const semPicked = pick(sem, [
                    "embedding_cosine_similarity",
                    "chunk_cosine_min",
                    "embedding_score_0_100",
                    "lexical_score_0_100",
                    "char_wb_trigram_cosine",
                    "tfidf_cosine_similarity",
                  ]);
                  const kwPicked = pick(kw, [
                    "matched_term_count",
                    "jd_term_count",
                    "bm25_alignment_0_100",
                    "keyword_overlap_base_0_100",
                    "title_term_count",
                    "title_matched_term_count",
                  ]);
                  const sampleMatched = Array.isArray((kw as any).sample_matched) ? (kw as any).sample_matched : [];

                  const blocks: Array<{ title: string; body: React.ReactNode }> = [
                    {
                      title: "Format",
                      body: (
                        <KeyValueList data={fmtPicked} />
                      ),
                    },
                    {
                      title: "Semantic",
                      body: (
                        <KeyValueList data={semPicked} />
                      ),
                    },
                    {
                      title: "Keywords",
                      body: (
                        <>
                          <KeyValueList data={kwPicked} />
                          {sampleMatched.length > 0 && (
                            <div className="mt-3">
                              <p className="text-[11px] font-bold uppercase tracking-wide text-ink-600 dark:text-ink-400">
                                Sample matched terms
                              </p>
                              <div className="mt-2 flex flex-wrap gap-2">
                                {sampleMatched.slice(0, 18).map((t: unknown) => {
                                  const s = asStr(t);
                                  if (!s) return null;
                                  return (
                                    <span
                                      key={s}
                                      className="rounded-full border border-black/10 bg-white/70 px-2.5 py-1 text-[11px] font-semibold text-ink-800 dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-200"
                                    >
                                      {s}
                                    </span>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </>
                      ),
                    },
                  ];

                  return blocks.map((b) => (
                    <div
                      key={b.title}
                      className="relative rounded-2xl border border-black/10 bg-white/70 p-3 dark:border-white/10 dark:bg-white/[0.05]"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-xs font-bold uppercase tracking-wide text-ink-600 dark:text-ink-400">
                          {b.title}
                        </p>
                        <button
                          type="button"
                          onClick={() =>
                            setInfoOpen((s) => ({
                              ...s,
                              [b.title.toLowerCase()]: !s[b.title.toLowerCase() as "format" | "semantic" | "keywords"],
                            }))
                          }
                          className="shrink-0 inline-flex items-center justify-center rounded-full border border-black/10 bg-white/80 p-2 text-ink-700 shadow-sm transition hover:bg-white hover:text-ink-950 dark:border-white/10 dark:bg-white/[0.06] dark:text-ink-200 dark:hover:bg-white/[0.10] dark:hover:text-white"
                          aria-label={`Explain ${b.title} terms`}
                          title="Explain terms"
                        >
                          <Info className="h-4 w-4" aria-hidden />
                        </button>
                      </div>
                      {b.body}

                      {b.title === "Format" && infoOpen.format && (
                        <div className="absolute right-3 top-10 z-10 w-[min(340px,calc(100%-24px))] rounded-2xl border border-black/10 bg-white/95 p-3 text-sm text-ink-700 shadow-lg backdrop-blur-md dark:border-white/10 dark:bg-black/70 dark:text-ink-200">
                          <p className="font-semibold text-ink-900 dark:text-white">Format signals</p>
                          <ul className="mt-2 list-disc space-y-1 pl-5">
                            <li>
                              <span className="font-semibold">word count</span>: extracted word count; very low counts often mean the file was scanned/image-heavy.
                            </li>
                            <li>
                              <span className="font-semibold">sections found</span>: detected headings (education, projects, skills, etc.) used for scanability.
                            </li>
                            <li>
                              <span className="font-semibold">layout scores</span>: simple heuristics for clarity (skills grouping, project bullet density, ordering).
                            </li>
                          </ul>
                        </div>
                      )}
                      {b.title === "Semantic" && infoOpen.semantic && (
                        <div className="absolute right-3 top-10 z-10 w-[min(340px,calc(100%-24px))] rounded-2xl border border-black/10 bg-white/95 p-3 text-sm text-ink-700 shadow-lg backdrop-blur-md dark:border-white/10 dark:bg-black/70 dark:text-ink-200">
                          <p className="font-semibold text-ink-900 dark:text-white">Semantic signals</p>
                          <ul className="mt-2 list-disc space-y-1 pl-5">
                            <li>
                              <span className="font-semibold">embedding cosine</span>: meaning similarity between resume and JD (0–1).
                            </li>
                            <li>
                              <span className="font-semibold">chunk cosine min</span>: the weakest-matching resume chunk; low means one section is off-topic vs the JD.
                            </li>
                            <li>
                              <span className="font-semibold">embedding score 0–100</span>: embeddings mapped to a 0–100 scale.
                            </li>
                            <li>
                              <span className="font-semibold">lexical score 0–100</span>: surface similarity (wording/terms), not meaning.
                            </li>
                          </ul>
                        </div>
                      )}
                      {b.title === "Keywords" && infoOpen.keywords && (
                        <div className="absolute right-3 top-10 z-10 w-[min(340px,calc(100%-24px))] rounded-2xl border border-black/10 bg-white/95 p-3 text-sm text-ink-700 shadow-lg backdrop-blur-md dark:border-white/10 dark:bg-black/70 dark:text-ink-200">
                          <p className="font-semibold text-ink-900 dark:text-white">Keyword signals</p>
                          <ul className="mt-2 list-disc space-y-1 pl-5">
                            <li>
                              <span className="font-semibold">matched JD terms</span>: important JD tokens that appear in the resume.
                            </li>
                            <li>
                              <span className="font-semibold">BM25 alignment</span>: ranking-style relevance between resume sentences and the JD.
                            </li>
                            <li>
                              <span className="font-semibold">keyword overlap</span>: raw important-token recall before BM25 blending.
                            </li>
                          </ul>
                        </div>
                      )}
                    </div>
                  ));
                })()}
              </div>
            </details>
          </section>

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
                  <PlanCard
                    key={i}
                    item={item}
                  />
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

