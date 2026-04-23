import type { ArchetypeItem, RunItem, ScoreResponse } from "./types";

const base = () => import.meta.env.VITE_API_BASE ?? "";

export async function fetchArchetypes(): Promise<ArchetypeItem[]> {
  const res = await fetch(`${base}/api/archetypes`);
  if (!res.ok) throw new Error("Could not load sample roles");
  const data = (await res.json()) as { items?: ArchetypeItem[] };
  return data.items ?? [];
}

export async function fetchRecentRuns(limit = 12): Promise<RunItem[]> {
  const res = await fetch(`${base}/api/runs?limit=${limit}`);
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
  if (import.meta.env.VITE_API_BASE)
    return " Check that VITE_API_BASE matches your live API URL and that the backend is up (e.g. Render free tier may be sleeping).";
  return " Run the API (e.g. make dev on http://localhost:8000). If you run the UI on another port, either use Vite (make dev-api + make dev-ui) or set VITE_API_BASE=http://localhost:8000.";
}

async function postScore(url: string, fd: FormData): Promise<Response> {
  return await fetch(url, { method: "POST", body: fd });
}

export async function scoreResume(fd: FormData): Promise<ScoreResponse> {
  // Primary: same-origin (works when UI is served by FastAPI or Vite dev/preview proxy).
  const primaryUrl = `${base()}/api/score`;

  const tryUrls = async (urls: string[]): Promise<Response> => {
    let last: Response | null = null;
    for (const url of urls) {
      try {
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
      throw new Error(`Could not reach the API.${apiBaseHint()}`);
    }
    return last;
  };

  // If POST /api/* hits a static server, it often returns 405.
  // In local dev (no VITE_API_BASE), retry known localhost backends. In production, only use the configured base.
  const candidates =
    base() === ""
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
