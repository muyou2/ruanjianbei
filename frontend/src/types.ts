export type Profile = {
  id?: number
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
