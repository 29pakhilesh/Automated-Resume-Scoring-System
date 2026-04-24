import type { ArchetypeItem, RunItem, ScoreResponse } from "./types";

const base = () => import.meta.env.VITE_API_BASE ?? "";
const baseUrl = () => base().replace(/\/+$/, "");

export async function fetchArchetypes(): Promise<ArchetypeItem[]> {
  const res = await fetch(`${baseUrl()}/api/archetypes`);
  if (!res.ok) throw new Error("Could not load sample roles");
  const data = (await res.json()) as { items?: ArchetypeItem[] };
  return data.items ?? [];
}

export async function fetchRecentRuns(limit = 12): Promise<RunItem[]> {
  const res = await fetch(`${baseUrl()}/api/runs?limit=${limit}`);
  if (!res.ok) return [];
  const data = (await res.json()) as { items?: RunItem[] };
  return data.items ?? [];
}

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg?: string }).msg) : String(d)))
      .join(" ");
  }
  return "Request failed";
}

function apiBaseHint(): string {
  if (import.meta.env.VITE_API_BASE) return " Check that VITE_API_BASE matches the API URL.";
  return " Run the API (e.g. make dev on http://localhost:8000). If you run the UI on another port, use the Vite proxy or set VITE_API_BASE=http://localhost:8000.";
}

async function postScore(url: string, fd: FormData): Promise<Response> {
  return await fetch(url, { method: "POST", body: fd, mode: "cors" });
}

export async function scoreResume(fd: FormData): Promise<ScoreResponse> {
  // Primary: same-origin (works when UI is served by FastAPI or Vite dev/preview proxy).
  const primaryUrl = `${baseUrl()}/api/score`;

  const tryUrls = async (urls: string[]): Promise<Response> => {
    let last: Response | null = null;
    let attempted: string | null = null;
    for (const url of urls) {
      try {
        attempted = url;
        const r = await postScore(url, fd);
        last = r;
        // If a server answered but doesn't support the method, keep trying known backends.
        if (r.status === 405) continue;
        return r;
      } catch {
        // Network errors (backend down / CORS / DNS) — try next candidate.
        continue;
      }
    }
    // If everything failed with network errors, surface a synthetic 503-like response shape.
    if (!last) {
      const u = attempted ?? primaryUrl;
      throw new Error(`Could not reach the API (${u}).${apiBaseHint()}`);
    }
    return last;
  };

  // If POST /api/* hits a static server, it often returns 405.
  // In local dev (no VITE_API_BASE), retry known localhost backends. In production, only use the configured base.
  const candidates =
    baseUrl() === ""
      ? [
          primaryUrl,
          "http://localhost:8000/api/score",
          "http://127.0.0.1:8000/api/score",
        ]
      : [primaryUrl];
  const res = await tryUrls(candidates);

  const data = (await res.json().catch(() => ({}))) as { detail?: unknown };
  if (!res.ok) {
    if (res.status === 405 || formatDetail(data.detail) === "Method Not Allowed") {
      throw new Error(
        `Scoring request was rejected (405 Method Not Allowed). The UI you opened isn't routing POST /api/score to FastAPI.${apiBaseHint()}`,
      );
    }
    throw new Error(formatDetail(data.detail));
  }
  return data as ScoreResponse;
}

export type ScoreProgress = {
  step: string;
  message?: string;
  pct?: number;
};

export async function startScoreJob(fd: FormData): Promise<{ job_id: string }> {
  const url = `${baseUrl()}/api/score_async`;
  const res = await fetch(url, { method: "POST", body: fd, mode: "cors" });
  const data = (await res.json().catch(() => ({}))) as { job_id?: string; detail?: unknown };
  if (!res.ok) throw new Error(formatDetail(data.detail));
  if (!data.job_id) throw new Error("Could not start scoring job (missing job_id).");
  return { job_id: data.job_id };
}

export function streamScoreJob(
  jobId: string,
  onProgress: (p: ScoreProgress) => void,
): Promise<ScoreResponse> {
  const url = `${baseUrl()}/api/score_events/${encodeURIComponent(jobId)}`;
  const es = new EventSource(url);

  return new Promise<ScoreResponse>((resolve, reject) => {
    let opened = false;
    let openWatchdog = 0;
    let settled = false;

    const cleanup = () => {
      window.clearTimeout(openWatchdog);
      es.removeEventListener("open", onOpen);
      es.removeEventListener("progress", onProgressEv);
      es.removeEventListener("result", onResultEv);
      es.removeEventListener("joberror", onJobErrEv);
      es.removeEventListener("error", onTransportErr);
      es.close();
    };

    const fail = (msg: string) => {
      if (settled) return;
      settled = true;
      cleanup();
      reject(new Error(msg));
    };

    const succeed = (data: ScoreResponse) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(data);
    };

    openWatchdog = window.setTimeout(() => {
      if (!opened && es.readyState !== EventSource.OPEN) {
        fail("Could not open live progress stream (SSE). Check your API URL / deployment.");
      }
    }, 12_000);

    const onOpen = () => {
      opened = true;
    };

    const onProgressEv = (e: MessageEvent) => {
      try {
        const p = JSON.parse(String(e.data)) as ScoreProgress;
        onProgress(p);
      } catch {
        onProgress({ step: "progress", message: String(e.data) });
      }
    };

    const onResultEv = (e: MessageEvent) => {
      try {
        const payload = JSON.parse(String(e.data)) as { result?: ScoreResponse };
        if (!payload?.result) {
          fail("Scoring completed but no result was returned.");
          return;
        }
        succeed(payload.result);
      } catch {
        fail("Scoring completed but result could not be parsed.");
      }
    };

    const onJobErrEv = (e: MessageEvent) => {
      try {
        const payload = JSON.parse(String(e.data)) as { message?: string };
        fail(payload.message || "Scoring failed.");
      } catch {
        fail("Scoring failed.");
      }
    };

    const onTransportErr = () => {
      if (settled) return;
      // EventSource emits `error` for both transient reconnect attempts and hard failures.
      // Only treat as fatal if we've opened and the socket is closed, or if it never opens.
      if (es.readyState === EventSource.CLOSED) {
        fail("Lost connection to the scoring stream. Please try again.");
      }
    };

    es.addEventListener("open", onOpen);
    es.addEventListener("progress", onProgressEv);
    es.addEventListener("result", onResultEv);
    es.addEventListener("joberror", onJobErrEv);
    es.addEventListener("error", onTransportErr);
  });
}
