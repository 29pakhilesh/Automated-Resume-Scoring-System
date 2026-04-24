import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BadgeCheck, Moon, Sun, Zap } from "lucide-react";
import { MeshBackground } from "@/components/MeshBackground";
import { ArchetypeChips } from "@/components/ArchetypeChips";
import { RecentRunsBar } from "@/components/RecentRunsBar";
import { ScoreFormCard } from "@/components/ScoreFormCard";
import { ResultsPanel } from "@/components/ResultsPanel";
import { DetailsPage } from "@/components/DetailsPage";
import { fetchArchetypes, fetchRecentRuns, startScoreJob, streamScoreJob } from "@/api";
import type { ArchetypeItem, RunItem, ScoreResponse } from "@/types";
import { applyTheme, getInitialTheme, type Theme } from "@/theme";
import logoPng from "@/assets/logo.jpeg";

const HERO_WORDS = ["measurable", "ATS-ready", "aligned", "compelling", "job-fit"];
const STORAGE_KEY = "rss.lastScoreResponse.v1";

export default function App() {
  const [positionTitle, setPositionTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [archetypes, setArchetypes] = useState<ArchetypeItem[]>([]);
  const [runs, setRuns] = useState<RunItem[]>([]);

  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<{ pct?: number; message?: string; step?: string } | null>(null);

  const resultsAnchor = useRef<HTMLDivElement>(null);
  const scoreSectionRef = useRef<HTMLDivElement>(null);
  const [theme, setTheme] = useState<Theme>(() => getInitialTheme());
  const [heroWordIdx, setHeroWordIdx] = useState(0);
  const [showSplash, setShowSplash] = useState(true);
  const [showTiles, setShowTiles] = useState(false);
  const [scrollPending, setScrollPending] = useState(false);

  const isDetails = typeof window !== "undefined" && window.location.pathname === "/details";

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    const prefersReduced = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    const delay = prefersReduced ? 350 : 1600;
    const id = window.setTimeout(() => setShowSplash(false), delay);
    return () => window.clearTimeout(id);
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => {
      setHeroWordIdx((i) => (i + 1) % HERO_WORDS.length);
    }, 2200);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [a, r] = await Promise.all([fetchArchetypes(), fetchRecentRuns(14)]);
        if (!cancelled) {
          setArchetypes(a);
          setRuns(r);
        }
      } catch {
        /* optional demo data — ignore */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshRuns = useCallback(async () => {
    try {
      setRuns(await fetchRecentRuns(14));
    } catch {
      /* ignore */
    }
  }, []);

  const handleArchetype = useCallback((item: ArchetypeItem) => {
    setPositionTitle(item.title);
    setJobDescription(item.jd);
  }, []);

  const handleSubmit = useCallback(async () => {
    setError(null);
    if (!positionTitle.trim()) {
      setError("Please enter a position title.");
      return;
    }
    if (jobDescription.trim().length < 40) {
      setError("Please paste a job description (at least 40 characters).");
      return;
    }
    if (!file) {
      setError("Please attach a PDF or DOCX resume.");
      return;
    }
    setLoading(true);
    setResult(null);
    setProgress({ pct: 1, message: "Starting…", step: "connected" });

    const fd = new FormData();
    fd.append("position_title", positionTitle.trim());
    fd.append("job_description", jobDescription);
    fd.append("file", file, file.name);

    try {
      const { job_id } = await startScoreJob(fd);
      const data = await streamScoreJob(job_id, (p) =>
        setProgress({ pct: p.pct, message: p.message, step: p.step }),
      );
      setResult(data);
      setProgress({ pct: 100, message: "Done", step: "done" });
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      } catch {
        // ignore
      }
      void refreshRuns();
      requestAnimationFrame(() => {
        resultsAnchor.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, [file, jobDescription, positionTitle, refreshRuns]);

  const scrollToScore = useCallback(() => {
    setShowTiles(true);
    setScrollPending(true);
  }, []);

  useEffect(() => {
    if (!showTiles || !scrollPending) return;
    // Wait for tiles to render before scrolling.
    const id = window.setTimeout(() => {
      scoreSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      setScrollPending(false);
    }, 0);
    return () => window.clearTimeout(id);
  }, [scrollPending, showTiles]);

  const openDetails = useCallback(() => {
    window.open("/details", "_blank", "noopener,noreferrer");
  }, []);

  if (isDetails) {
    return (
      <div className="min-h-screen text-ink-900 dark:text-ink-100">
        <MeshBackground />
        <DetailsPage />
      </div>
    );
  }

  return (
    <div className="min-h-screen text-ink-900 dark:text-ink-100">
      <MeshBackground />

      <AnimatePresence>
        {showSplash && (
          <motion.div
            key="splash"
            className="fixed inset-0 z-[200] grid place-items-center bg-white/95 backdrop-blur-xl dark:bg-black/96"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          >
            <motion.div
              className="flex flex-col items-center gap-4"
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
            >
              <motion.div
                layoutId="brandLogo"
                className="relative h-24 w-52 overflow-hidden rounded-3xl bg-white shadow-2xl shadow-black/10 ring-1 ring-black/10 dark:bg-white dark:ring-white/10"
              >
                <img src={logoPng} alt="Resume Score" className="h-full w-full object-contain p-2" />
              </motion.div>
              <motion.p
                className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-600 dark:text-ink-300"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.12, duration: 0.45 }}
              >
                Resume Score
              </motion.p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <a
        href="#main"
        className="absolute left-[-9999px] top-4 z-[100] rounded-lg bg-white px-4 py-2 text-sm font-medium text-ink-950 shadow-lg focus:left-4 dark:bg-ink-900 dark:text-ink-50"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-40 border-b border-black/5 bg-white/50 backdrop-blur-xl dark:border-white/5 dark:bg-ink-950/40">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-6">
          <div className="flex items-center gap-3">
            <motion.div
              layoutId="brandLogo"
              className="relative h-12 w-24 overflow-hidden rounded-2xl bg-white shadow-lg shadow-black/10 ring-1 ring-black/10 dark:bg-white dark:ring-white/10"
            >
              <img src={logoPng} alt="Resume Score" className="h-full w-full object-contain p-1.5" />
            </motion.div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-500 dark:text-ink-500">
                Resume scoring
              </p>
              <p className="text-sm font-semibold text-ink-950 dark:text-white">Resume Score</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <motion.button
              type="button"
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
              className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-black/[0.03] px-3 py-2 text-xs font-semibold text-ink-700 shadow-sm transition hover:bg-black/[0.06] focus:outline-none focus-visible:ring-4 focus-visible:ring-accent/20 dark:border-white/10 dark:bg-white/5 dark:text-ink-200 dark:hover:bg-white/10"
              aria-label="Toggle color theme"
            >
              <AnimatePresence mode="wait" initial={false}>
                {theme === "dark" ? (
                  <motion.span
                    key="moon"
                    initial={{ opacity: 0, rotate: -20, scale: 0.9 }}
                    animate={{ opacity: 1, rotate: 0, scale: 1 }}
                    exit={{ opacity: 0, rotate: 20, scale: 0.9 }}
                    transition={{ duration: 0.18 }}
                    className="inline-flex items-center gap-2"
                  >
                    <Moon className="h-4 w-4 text-ink-900 dark:text-ink-100" aria-hidden />
                    Dark
                  </motion.span>
                ) : (
                  <motion.span
                    key="sun"
                    initial={{ opacity: 0, rotate: 20, scale: 0.9 }}
                    animate={{ opacity: 1, rotate: 0, scale: 1 }}
                    exit={{ opacity: 0, rotate: -20, scale: 0.9 }}
                    transition={{ duration: 0.18 }}
                    className="inline-flex items-center gap-2"
                  >
                    <Sun className="h-4 w-4 text-ink-900 dark:text-ink-100" aria-hidden />
                    Light
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          </div>
        </div>
      </header>

      <motion.main
        id="main"
        className="mx-auto max-w-6xl px-4 pb-20 pt-10 md:px-6 md:pt-14"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      >
        <section className="mb-14 max-w-2xl pt-6 md:pt-10">
          <motion.h1
            className="text-balance text-4xl font-bold tracking-tight text-ink-950 md:text-5xl dark:text-white"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.05, ease: [0.22, 1, 0.36, 1] }}
          >
            Make every application{" "}
            <span className="relative inline-flex min-w-[10ch] items-baseline">
              <AnimatePresence mode="wait" initial={false}>
                <motion.span
                  key={HERO_WORDS[heroWordIdx]}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
                  className="bg-gradient-to-r from-sky-600 to-blue-700 bg-clip-text text-transparent dark:from-sky-300 dark:to-blue-400"
                >
                  {HERO_WORDS[heroWordIdx]}
                </motion.span>
              </AnimatePresence>
            </span>
          </motion.h1>
          <motion.p
            className="mt-4 text-lg leading-relaxed text-ink-600 dark:text-ink-300"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
          >
            Upload your resume and job description to get a clear score, key strengths, and prioritized improvements—plus
            optional AI coaching for a polished, role-aligned version.
          </motion.p>

          <motion.div
            className="mt-6 flex flex-wrap gap-2"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
          >
            {[
              { icon: <Zap className="h-4 w-4" aria-hidden />, text: "Fast scoring" },
              { icon: <BadgeCheck className="h-4 w-4" aria-hidden />, text: "Actionable fixes" },
              { icon: <BadgeCheck className="h-4 w-4" aria-hidden />, text: "Format + semantic fit" },
            ].map((b) => (
              <span
                key={b.text}
                className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white/60 px-3 py-1.5 text-xs font-semibold text-ink-800 shadow-sm backdrop-blur-md dark:border-white/10 dark:bg-white/[0.05] dark:text-ink-200"
              >
                {b.icon}
                {b.text}
              </span>
            ))}
          </motion.div>
          <motion.div
            className="mt-7 flex flex-wrap items-center gap-3"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.24, ease: [0.22, 1, 0.36, 1] }}
          >
            <motion.button
              type="button"
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.99 }}
              onClick={scrollToScore}
              className="inline-flex items-center justify-center rounded-xl bg-ink-950 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-black/10 transition hover:bg-ink-900 dark:bg-white dark:text-ink-950 dark:hover:bg-white/90"
            >
              Score your resume
            </motion.button>
            <p className="text-sm text-ink-600 dark:text-ink-400">Takes about a minute. You’ll get scores + next steps.</p>
          </motion.div>
        </section>

        <div ref={scoreSectionRef} className="scroll-mt-28">
          <AnimatePresence initial={false}>
            {(showTiles || loading || Boolean(result) || Boolean(error)) && (
              <motion.div
                key="tiles"
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 18 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              >
                <ArchetypeChips items={archetypes} onPick={handleArchetype} disabled={loading} />
                <RecentRunsBar runs={runs} />

                <motion.div
                  ref={resultsAnchor}
                  className="grid items-stretch gap-6 lg:grid-cols-2 lg:gap-8"
                  initial="hidden"
                  animate="show"
                  variants={{
                    hidden: { opacity: 0 },
                    show: { opacity: 1, transition: { staggerChildren: 0.06 } },
                  }}
                >
                  <motion.div variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } }}>
                    <ScoreFormCard
                      positionTitle={positionTitle}
                      onPositionTitleChange={setPositionTitle}
                      jobDescription={jobDescription}
                      onJobDescriptionChange={setJobDescription}
                      file={file}
                      onFileChange={setFile}
                      loading={loading}
                  progress={progress}
                      onSubmit={handleSubmit}
                    />
                  </motion.div>
                  <motion.div variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } }}>
                    <ResultsPanel result={result} error={error} loading={loading} onViewDetails={openDetails} />
                  </motion.div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.main>

      <footer className="relative py-12 text-center text-xs leading-relaxed text-ink-500">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-14 bg-gradient-to-b from-black/[0.03] to-transparent dark:from-white/[0.04]" />
        <p className="relative mx-auto max-w-xl px-4 text-ink-600/80 dark:text-ink-500">
          Scores combine structure checks, lexical signals, and transformer embeddings. Optional AI output is advisory
          only—not a hiring decision.
        </p>
      </footer>
    </div>
  );
}
