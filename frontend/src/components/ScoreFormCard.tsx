import { useCallback, useId, useMemo, useState } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";
import { ArrowRight, FileText, UploadCloud } from "lucide-react";

const ACCEPT = ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

type Props = {
  positionTitle: string;
  onPositionTitleChange: (v: string) => void;
  jobDescription: string;
  onJobDescriptionChange: (v: string) => void;
  file: File | null;
  onFileChange: (f: File | null) => void;
  loading: boolean;
  progress?: { pct?: number; message?: string; step?: string } | null;
  onSubmit: () => void;
};

export function ScoreFormCard({
  positionTitle,
  onPositionTitleChange,
  jobDescription,
  onJobDescriptionChange,
  file,
  onFileChange,
  loading,
  progress,
  onSubmit,
}: Props) {
  const inputId = useId();
  const [dragOver, setDragOver] = useState(false);

  const progressPct = progress?.pct ?? 0;

  const steps = useMemo(
    () => [
      { step: "upload_received", label: "Upload received" },
      { step: "extracting_text", label: "Extracting text" },
      { step: "scoring", label: "Scoring" },
      { step: "finalizing", label: "Finalizing" },
    ],
    [],
  );

  const activeLabel = progress?.message?.trim()
    ? progress.message
    : loading
      ? "Working…"
      : "";

  const pickFile = useCallback(
    (f: File | null) => {
      if (!f) {
        onFileChange(null);
        return;
      }
      const n = f.name.toLowerCase();
      if (!n.endsWith(".pdf") && !n.endsWith(".docx")) return;
      onFileChange(f);
    },
    [onFileChange],
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    pickFile(f ?? null);
  };

  return (
    <motion.section
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="h-full"
    >
      <div className="h-full rounded-3xl bg-gradient-to-b from-black/10 to-black/0 p-[1px] dark:from-white/12 dark:to-white/0">
        <div className="relative flex h-full flex-col overflow-hidden rounded-3xl bg-white/70 p-5 shadow-card-light backdrop-blur-xl transition-colors md:p-6 dark:bg-white/[0.035] dark:shadow-card">
          <div className="pointer-events-none absolute -right-24 -top-24 h-56 w-56 rounded-full bg-black/[0.05] blur-3xl dark:bg-white/[0.05]" />
      <header className="relative mb-6 border-b border-black/10 pb-4 dark:border-white/10">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-700 dark:text-ink-300">Analyze</p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight text-ink-950 dark:text-white">Score your resume</h2>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-700 dark:text-ink-300">
          Add the target role and job description, attach a PDF or DOCX, and get structured feedback in seconds.
        </p>
      </header>

      <form
        className="relative flex-1 space-y-4"
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-ink-600 dark:text-ink-400">
            Position title
          </span>
          <input
            value={positionTitle}
            onChange={(e) => onPositionTitleChange(e.target.value)}
            autoComplete="organization-title"
            placeholder="e.g. Senior Backend Engineer"
            className="w-full rounded-xl border border-black/10 bg-white/80 px-4 py-2.5 text-sm text-ink-950 placeholder:text-ink-500 outline-none transition focus:border-black/30 focus:ring-4 focus:ring-black/10 dark:border-white/10 dark:bg-ink-950/60 dark:text-white dark:placeholder:text-ink-500 dark:focus:border-white/25 dark:focus:ring-white/10"
          />
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-ink-600 dark:text-ink-400">
            Job description
          </span>
          <textarea
            rows={7}
            value={jobDescription}
            onChange={(e) => onJobDescriptionChange(e.target.value)}
            placeholder="Paste responsibilities, requirements, and tech stack (min. 40 characters)."
            className="w-full resize-y rounded-xl border border-black/10 bg-white/80 px-4 py-2.5 text-sm leading-relaxed text-ink-950 placeholder:text-ink-500 outline-none transition focus:border-black/30 focus:ring-4 focus:ring-black/10 dark:border-white/10 dark:bg-ink-950/60 dark:text-white dark:placeholder:text-ink-500 dark:focus:border-white/25 dark:focus:ring-white/10"
          />
        </label>

        <div>
          <span
            id={`${inputId}-file`}
            className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-ink-600 dark:text-ink-400"
          >
            Resume file
          </span>
          <label
            htmlFor={`${inputId}-input`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={clsx(
              "relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-4 py-3 transition-colors",
              dragOver
                ? "border-black/30 bg-black/[0.03] dark:border-white/25 dark:bg-white/[0.04]"
                : "border-black/15 bg-white/60 hover:border-black/30 dark:border-white/15 dark:bg-ink-950/40 dark:hover:border-white/25",
              file && "border-solid border-black/20 bg-black/[0.02] dark:border-white/20 dark:bg-white/[0.03]",
            )}
          >
            <input
              id={`${inputId}-input`}
              type="file"
              accept={ACCEPT}
              className="sr-only"
              onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
            />
            <div className="mb-1.5 flex h-8 w-8 items-center justify-center rounded-2xl bg-black/[0.05] text-ink-900 dark:bg-white/[0.06] dark:text-white">
              {file ? <FileText className="h-4.5 w-4.5" aria-hidden /> : <UploadCloud className="h-4.5 w-4.5" aria-hidden />}
            </div>
            <p className="text-center text-[12.5px] font-semibold leading-snug text-ink-950 dark:text-white">
              {file ? file.name : "Drop PDF or DOCX here, or click to browse"}
            </p>
            <p className="mt-0.5 text-center text-[11px] text-ink-600 dark:text-ink-500">Max 5 MB</p>
          </label>
        </div>

        <motion.button
          type="submit"
          disabled={loading}
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.99 }}
          className="group relative flex w-full items-center justify-center overflow-hidden rounded-xl bg-brand-navy py-3 text-sm font-semibold text-white shadow-lg shadow-black/10 transition hover:bg-[#182038] disabled:cursor-not-allowed disabled:opacity-55 dark:bg-white dark:text-ink-950 dark:hover:bg-white/90"
        >
          <span className="relative z-10 inline-flex items-center">
            {loading ? "Scoring your resume…" : "Score my resume"}
            {!loading && (
              <span className="ml-2 inline-flex w-5 justify-end overflow-hidden">
                <ArrowRight
                  className="h-4 w-4 translate-x-2 opacity-0 transition duration-200 ease-out group-hover:translate-x-0 group-hover:opacity-100"
                  aria-hidden
                />
              </span>
            )}
          </span>
          {loading && (
            <span className="absolute inset-0 bg-white/10 animate-shimmer" aria-hidden />
          )}
        </motion.button>

        {loading && (
          <div className="pt-3">
            <div className="flex items-center justify-between gap-3 text-xs">
              <p className="font-semibold text-ink-800 dark:text-ink-200">{activeLabel}</p>
              <p className="tabular-nums text-ink-600 dark:text-ink-500">
                {progressPct ? `${Math.round(progressPct)}%` : ""}
              </p>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-sky-500 to-blue-600"
                initial={{ width: "0%" }}
                animate={{ width: `${Math.min(99, Math.max(3, progressPct || 3))}%` }}
                transition={{ type: "spring", stiffness: 120, damping: 18 }}
              />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-ink-600 dark:text-ink-500">
              {steps.map((s) => (
                <div key={s.step} className="flex items-center gap-2">
                  <span
                    className={clsx(
                      "h-1.5 w-1.5 rounded-full",
                      progress?.step === s.step || (progressPct && progressPct >= 95 && s.step === "finalizing")
                        ? "bg-ink-900 dark:bg-white"
                        : progressPct && progressPct > 0
                          ? "bg-black/30 dark:bg-white/30"
                          : "bg-black/20 dark:bg-white/20",
                    )}
                  />
                  <span
                    className={clsx(
                      progress?.step === s.step && "text-ink-900 dark:text-ink-200",
                    )}
                  >
                    {s.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <p className="text-center text-xs text-ink-600 dark:text-ink-500">Tip: PDFs and DOCX are supported.</p>
      </form>
        </div>
      </div>
    </motion.section>
  );
}
