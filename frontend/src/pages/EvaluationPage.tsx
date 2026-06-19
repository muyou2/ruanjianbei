import { useEffect, useState } from 'react'
import { Award, CheckCircle2, Target } from 'lucide-react'
import { api } from '../api'
import { Button, Card, EmptyState, PageHeader } from '../components'
import type { QuizQuestion } from '../types'

export default function EvaluationPage() {
  const [resourceId, setResourceId] = useState<number | null>(null)
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  useEffect(() => { api<any>('/api/quizzes').then(data => { if (data) { setResourceId(data.resource_id); setQuestions(data.questions) } }).catch(() => null) }, [])
  const submit = async () => {
    if (!resourceId) return
    setLoading(true)
    try { setResult(await api('/api/evaluations/submit', { method: 'POST', body: JSON.stringify({ resource_id: resourceId, answers: questions.map(q => ({ question_id: q.id, answer: answers[q.id] || '' })) }) })) }
    finally { setLoading(false) }
  }
  return (
    <>
      <PageHeader eyebrow="Learning Evaluation" title="从答题结果回到下一步学习行动" description="完成四类题目后，系统给出正确率、薄弱知识点和复习建议，并把结果动态写回学生画像。" />
      {!questions.length ? <EmptyState title="还没有可评估的题目" text="请先前往资源生成页，创建一个完整学习资源包。" /> :
      <div className="grid gap-6 xl:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          {questions.map((q, i) => <Card key={q.id}>
            <div className="flex items-center justify-between"><span className="text-xs font-bold text-violet-600">第 {i + 1} 题 · {q.knowledge_point}</span><span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] text-slate-500">{q.type}</span></div>
            <h3 className="mt-3 font-bold leading-7">{q.question}</h3>
            {q.options.length ? <div className="mt-4 grid gap-2 sm:grid-cols-2">{q.options.map(option => <label key={option} className={`cursor-pointer rounded-2xl border p-3 text-sm transition ${answers[q.id] === option ? 'border-violet-400 bg-violet-50 text-violet-800' : 'border-slate-100 bg-slate-50'}`}><input className="mr-2" type="radio" name={q.id} checked={answers[q.id] === option} onChange={() => setAnswers(a => ({ ...a, [q.id]: option }))} />{option}</label>)}</div>
            : <textarea value={answers[q.id] || ''} onChange={e => setAnswers(a => ({ ...a, [q.id]: e.target.value }))} className="mt-4 min-h-28 w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm outline-none focus:border-violet-400" placeholder="输入你的答案…" />}
            {result && <div className={`mt-4 rounded-2xl p-4 text-sm ${result.detail[i]?.correct ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-900'}`}><div className="font-bold">{result.detail[i]?.correct ? '回答正确' : '建议复习'}</div><div className="mt-1 leading-6">{q.explanation}</div></div>}
          </Card>)}
          <Button loading={loading} onClick={submit} className="w-full">提交答案并生成评估报告</Button>
        </div>
        <div>
          {result ? <Card className="sticky top-6">
            <div className="text-center"><div className="mx-auto grid h-14 w-14 place-items-center rounded-3xl bg-gradient-to-br from-amber-400 to-orange-500 text-white"><Award /></div><div className="mt-3 text-5xl font-black">{result.score}</div><div className="text-xs text-slate-400">综合得分</div></div>
            <div className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-2xl bg-emerald-50 p-3 text-center"><div className="text-xl font-black text-emerald-700">{result.correct_count}</div><div className="text-xs text-emerald-700">答对</div></div><div className="rounded-2xl bg-slate-50 p-3 text-center"><div className="text-xl font-black">{result.total}</div><div className="text-xs text-slate-500">总题数</div></div></div>
            <div className="mt-5"><div className="flex items-center gap-2 font-black"><Target className="h-4 w-4 text-violet-600" />薄弱知识点</div><div className="mt-2 flex flex-wrap gap-2">{result.weak_points.length ? result.weak_points.map((w: string) => <span key={w} className="rounded-full bg-rose-50 px-3 py-1 text-xs font-bold text-rose-700">{w}</span>) : <span className="text-sm text-emerald-600">暂无明显薄弱点</span>}</div></div>
            <div className="mt-5"><div className="flex items-center gap-2 font-black"><CheckCircle2 className="h-4 w-4 text-emerald-600" />下一步建议</div><ul className="mt-2 space-y-2 text-sm leading-6 text-slate-600">{result.suggestions.map((s: string) => <li key={s}>• {s}</li>)}</ul></div>
          </Card> : <Card><div className="text-center text-sm leading-7 text-slate-500">完成左侧题目并提交后，这里将生成多维评估报告，并自动更新你的学习画像。</div></Card>}
        </div>
      </div>}
    </>
  )
}
