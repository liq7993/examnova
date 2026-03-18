export type Screen = "splash" | "welcome" | "features" | "setup" | "home";
export type WorkspaceTab = "study" | "thinking";

export type SavedSettings = {
  backendUrl: string;
  baseUrl: string;
  model: string;
  demoMode: boolean;
  mathpixEnabled: boolean;
  mathpixAppId: string;
  mathpixEndpoint: string;
  onboardingComplete: boolean;
};

export type ConnectionState =
  | { status: "idle"; message: string }
  | { status: "loading"; message: string }
  | { status: "success"; message: string }
  | { status: "error"; message: string };

export type StudyResponse = {
  knowledge_points: string[];
  difficulty: string;
  explanation_mode: string;
  explanation: string;
  solution_steps: string[];
  formula_notes: string[];
  novice_explain: string;
  review_schedule: string[];
  time_plan: string[];
  memory_tips: string[];
  exam_tricks: string[];
  diagram_hint: string;
  variant_questions: string[];
  mini_quiz: string[];
  self_questions: string[];
  practice_set: string[];
  examples: string[];
  exam_focus_prediction: string[];
  next_action: string;
  confidence_note: string;
  risk_notice: string;
  score_breakdown: string[];
};

export type ThinkingResponse = {
  mode: string;
  title: string;
  outline: string[];
  content: string;
  rewrite_options: string[];
  key_points: string[];
  tone_tags: string[];
  export_title: string;
  summary: string;
  confidence_note: string;
  reflection_prompt: string;
  review_bridge: string[];
  action_list: string[];
};

export type StudyReviewMode = "auto" | "cram" | "standard";

export type StudySessionState = {
  session_key: string;
  course: string;
  question_text: string;
  topic_label: string;
  knowledge_points: string[];
  mini_quiz: string[];
  memory_tips: string[];
  review_mode: StudyReviewMode;
  strategy_name: "cram" | "standard";
  started_at: string;
  last_activity_at: string;
  focused_seconds: number;
  wall_elapsed_minutes: number;
  focused_minutes: number;
  curve_due_count: number;
  focus_due_count: number;
  curve_ack_stage: number;
  focus_ack_stage: number;
  next_curve_due_at: string | null;
  next_focus_due_at: string | null;
  next_curve_prompt: string | null;
  next_focus_prompt: string | null;
};
