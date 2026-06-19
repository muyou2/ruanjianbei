export type Profile = {
  id?: number
  demo_key?: string | null
  display_name: string
  is_active?: boolean
  major: string
  grade: string
  knowledge_level: string
  learning_goal: string
  weak_points: string[]
  learning_style: string
  resource_preference: string[]
  mistake_history: string[]
  source_text?: string
  updated_at?: string
}

export type Citation = {
  chunk_id: string
  document_id?: number
  title: string
  content: string
  score: number
  retrieval_backend?: string
  retrieval_mode?: string
}

export type QuizQuestion = {
  id: string
  type: 'single_choice' | 'true_false' | 'short_answer' | 'code'
  question: string
  options: string[]
  answer: string
  explanation: string
  knowledge_point: string
}

export type Resource = {
  id: number
  topic: string
  content: Record<string, any>
  review: Record<string, any>
  created_at: string
}

export type GenerationMeta = {
  provider?: string
  model?: string
  label?: string
  used_real_model?: boolean
  fallback_used?: boolean
  rag_enhanced?: boolean
  error?: string | null
}
