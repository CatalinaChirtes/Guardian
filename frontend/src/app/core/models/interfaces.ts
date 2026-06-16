export interface TutorSession {
  id: string;
  user_id: string;
  session_type: 'chat' | 'challenge' | 'theory';
  exercise_id: string | null;
  title: string | null;
  llm_provider: string;
  total_attempts: number;
  puzzle_triggered: boolean;
  solved: boolean;
  created_at: string;
  ended_at: string | null;
}

export interface SessionDetail extends TutorSession {
  messages: ChatMessage[];
  last_code: string | null;
  last_language: string | null;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'student' | 'tutor';
  content: string;
  mode: 'socratic' | 'theory' | 'puzzle' | 'puzzle_result' | 'error' | 'code_police_fallback' | null;
  llm_provider: string | null;
  llm_model: string | null;
  latency_ms: number | null;
  sources: string | null;
  feedback: string | null;
  created_at: string;
}

export interface Exercise {
  id: string;
  question: string;
  starter_code: string;
  difficulty: 'introductory' | 'interview' | 'competition';
}

export interface CurriculumDocument {
  id: string;
  filename: string;
  chunk_count: number;
  uploaded_at: string;
}

export type WsIncoming =
  | { type: 'response'; content: string; message_id?: string; mode?: string; sources?: string }
  | { type: 'token'; content: string }
  | { type: 'done' }
  | { type: 'puzzle'; lines: string[]; content?: string; language?: string }
  | { type: 'analysis'; language?: string; is_valid?: boolean; errors?: string[] }
  | { type: 'puzzle_result'; is_correct: boolean; message?: string; challenge_solved?: boolean }
  | { type: 'error'; message: string };
