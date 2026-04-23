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
