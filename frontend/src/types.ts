export type Subscores = {
  format_and_structure?: number;
  semantic_fit_vs_job_description?: number;
  keyword_coverage_vs_job_description?: number;
};

export type ImprovementItem = {
  area?: string;
  severity?: string;
  why?: string;
  fix?: string;
  snippet?: {
    kind?: string;
    offset?: number;
    cosine?: number;
    text_preview?: string;
  };
  snippet_image_mime?: string;
  snippet_image_base64?: string;
  snippet_image_url?: string;
  /** True when `snippet_image_url` points at stacked full-document preview with highlights */
  snippet_full_document_preview?: boolean;
};

export type AiCoach = {
  provider?: string;
  model?: string;
  text?: string;
  error?: string;
};

export type ScoreResponse = {
  overall_score?: number;
  subscores?: Subscores;
  feedback?: string[];
  improvement_plan?: ImprovementItem[];
  ai_coach?: AiCoach;
  extracted_text_preview?: string;
  filename?: string;
  position_title_considered?: string;
  weights_applied?: {
    format?: number;
    semantic?: number;
    keywords?: number;
  };
  details?: {
    format?: Record<string, unknown>;
    semantic?: Record<string, unknown>;
    keywords?: Record<string, unknown>;
  };
  gap_report?: {
    missing_keywords_from_jd?: string[];
    keyword_stats?: {
      jd_term_count?: number;
      matched_term_count?: number;
    };
    semantic_signals?: Record<string, unknown>;
    format_highlights?: {
      sections_found?: string[];
      word_count?: number;
    };
    weakest_resume_segments_vs_jd?: Array<{
      offset?: number;
      cosine?: number;
      preview?: string;
    }>;
  };
  weak_section_snippet?: {
    mime?: string;
    url?: string;
    offset?: number;
    cosine?: number;
  };
  /** Stacked pages + approximate highlight bands for weak JD-alignment chunks */
  annotated_document_preview?: {
    mime?: string;
    url?: string;
    marked_regions?: number;
  };
};

export type ArchetypeItem = {
  id: string;
  title: string;
  tags: string[];
  jd: string;
};

export type RunItem = {
  id: number;
  created_at: string | null;
  filename: string;
  position_title: string;
  overall_score: number;
  format_score: number;
  semantic_score: number;
  keyword_score: number;
};
