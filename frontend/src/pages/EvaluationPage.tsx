import { useEffect, useState } from 'react'
import { AlertTriangle, Award, CheckCircle2, Target } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { Button, Card, EmptyState, PageHeader } from '../components'
import type { QuizQuestion } from '../types'

export default function EvaluationPage() {
  const [searchParams] = useSearchParams()
  const [resourceId, setResourceId] = useState<number | null>(null)
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const requested = searchParams.get('resource_id')
    api<any>(`/api/quizzes${requested ? `?resource_id=${requested}` : ''}`).then(data => {
      if (data) {
        setResourceId(data.resource_id)
        setQuestions(data.questions)
      }
    }).catch(() => null)
  }, [searchParams])

  const submit = async () => {
    if (!resourceId) return
    setLoading(true); setError('')
    try {
      setResult(await api('/api/evaluations/submit', {
        method: 'POST',
        body: JSON.stringify({
          resource_id: resourceId,
          answers: questions.map(question => ({ question_id: question.id, answer: answers[question.id] || '' })),
        }),
      }))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '测评提交失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeader eyebrow="Learning Evaluation" title="真实判分，并把错误写回画像" description="选择和判断精确匹配；简答采用 MVP 关键词评分；代码题只检查关键语句，不假装在服务器执行代码。" />
      {!questions.length ? <EmptyState title="当前学生还没有可评估题目" text="请先生成该学生的学习资源包。" /> :
      <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
        <div className="space-y-4">
          {questions.map((question, index) => <Card key={question.id}>
            <div className="flex items-center justify-between"><span className="text-xs font-bold text-violet-600">第 {index + 1} 题 · {question.knowledge_point}</span><span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] text-slate-500">{question.type} · 25 分</span></div>
            {question.type === 'short_answer' && <div className="mt-2 text-xs font-bold text-amber-700">关键词覆盖度 MVP 评分</div>}
            {question.type === 'code' && <div className="mt-2 text-xs font-bold text-amber-700">关键语句检查，未接入安全沙箱执行</div>}
            <h3 className="mt-3 font-bold leading-7">{question.question}</h3>
            {question.options.length ? <div className="mt-4 grid gap-2 sm:grid-cols-2">{question.options.map(option => <label key={option} className={`cursor-pointer rounded-2xl border p-3 text-sm transition ${answers[question.id] === option ? 'border-violet-400 bg-violet-50 text-violet-800' : 'border-slate-100 bg-slate-50'}`}><input className="mr-2" type="radio" name={question.id} checked={answers[question.id] === option} onChange={() => setAnswers(previous => ({ ...previous, [question.id]: option }))} />{option}</label>)}</div>
              : <textarea value={answers[question.id] || ''} onChange={event => setAnswers(previous => ({ ...previous, [question.id]: event.target.value }))} className="mt-4 min-h-32 w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 font-mono text-sm outline-none focus:border-violet-400" placeholder={question.type === 'code' ? '输入代码。系统只做关键语句检查，不会执行。' : '输入你的解释…'} />}
            {result && <div className={`mt-4 rounded-2xl p-4 text-sm ${result.detail[index]?.correct ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-900'}`}>
              <div className="flex justify-between font-bold"><span>{result.detail[index]?.correct ? '达到当前判分标准' : '需要复习'}</span><span>{result.detail[index]?.points} / 25</span></div>
              <div className="mt-1 text-xs">{result.detail[index]?.scoring_method}</div>
              <div className="mt-2 leading-6">{question.explanation}</div>
              {result.detail[index]?.manual_review && <div className="mt-2 flex items-center gap-2 rounded-xl bg-white/70 p-2 text-xs"><AlertTriangle className="h-4 w-4" />代码未执行，仍需人工核验运行结果和边界情况。</div>}
            </div>}
          </Card>)}
          <Button loading={loading} onClick={submit} className="w-full">提交答案、保存评估并更新画像</Button>
          {error && <div className="rounded-2xl bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
        </div>
        <div>
          {result ? <div className="sticky top-6 space-y-4">
            <Card>
              <div className="text-center"><div className="mx-auto grid h-14 w-14 place-items-center rounded-3xl bg-gradient-to-br from-amber-400 to-orange-500 text-white"><Award /></div><div className="mt-3 text-5xl font-black">{result.score}</div><div className="text-xs text-slate-400">总分 / 100</div></div>
              <div className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-2xl bg-emerald-50 p-3 text-center"><div className="text-xl font-black text-emerald-700">{result.correct_count}</div><div className="text-xs text-emerald-700">达标题数</div></div><div className="rounded-2xl bg-slate-50 p-3 text-center"><div className="text-xl font-black">{result.question_count}</div><div className="text-xs text-slate-500">总题数</div></div></div>
              <div className="mt-5"><div className="flex items-center gap-2 font-black"><Target className="h-4 w-4 text-violet-600" />薄弱知识点</div><div className="mt-2 flex flex-wrap gap-2">{result.weak_points.length ? result.weak_points.map((item: string) => <span key={item} className="rounded-full bg-rose-50 px-3 py-1 text-xs font-bold text-rose-700">{item}</span>) : <span className="text-sm text-emerald-600">暂无新增薄弱点</span>}</div></div>
              <div className="mt-5"><div className="flex items-center gap-2 font-black"><CheckCircle2 className="h-4 w-4 text-emerald-600" />下一步建议</div><ul className="mt-2 space-y-2 text-sm leading-6 text-slate-600">{result.suggestions.map((item: string) => <li key={item}>• {item}</li>)}</ul></div>
              <div className="mt-5 border-t border-slate-100 pt-4"><div className="font-black">本次更新后的知识点掌握度</div><div className="mt-3 space-y-2">{result.mastery?.map((item: any) => <div key={item.knowledge_point} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-xs"><span>{item.knowledge_point}</span><span className="font-bold text-violet-700">{item.mastery}%</span></div>)}</div></div>
              {result.learning_plan && <div className="mt-5 rounded-2xl bg-violet-50 p-4"><div className="font-black text-violet-800">学习计划已自动推进</div><div className="mt-1 text-xs text-violet-700">针对性练习和测评复盘已完成，当前进度 {result.learning_plan.progress}%（{result.learning_plan.completed}/{result.learning_plan.total}）。</div><Link to={`/resources?resource=${result.learning_plan.resource_id}`} className="mt-3 inline-block rounded-xl bg-white px-3 py-2 text-xs font-bold text-violet-700">返回资源中心继续学习</Link></div>}
            </Card>
            <Card className="border-violet-100 bg-violet-50/80">
              <h3 className="font-black text-violet-800">画像写回结果</h3>
              <div className="mt-3 text-xs text-violet-600">更新对象：{result.profile_after?.display_name}</div>
              <div className="mt-3 space-y-2">{result.profile_changes.length ? result.profile_changes.map((change: any) => <div key={change.field} className="rounded-xl bg-white p-3 text-xs"><div className="font-bold">{change.field}</div><div className="mt-1 text-slate-500">更新前：{Array.isArray(change.before) ? change.before.join('、') : String(change.before ?? '无')}</div><div className="mt-1 text-violet-800">更新后：{Array.isArray(change.after) ? change.after.join('、') : String(change.after ?? '无')}</div></div>) : <div className="text-sm text-slate-500">本次没有新增薄弱点。</div>}</div>
            </Card>
          </div> : <Card><div className="text-center text-sm leading-7 text-slate-500">提交后将保存数据库、展示逐题判分依据，并显示画像更新前后的差异。</div></Card>}
        </div>
      </div>}
    </>
  )
}
