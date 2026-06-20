import { useEffect, useState } from 'react'
import { Bot, CheckCircle2, Circle, Clock3, Download, GitBranch, ShieldCheck, ThumbsDown, ThumbsUp, UserRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, consumeSSE } from '../api'
import { Button, Card, EmptyState, Markdown, Mermaid, PageHeader } from '../components'
import type { Citation, GenerationMeta, LearningPlan, Profile, Resource } from '../types'

const tabs = [
  ['learning_path', '学习路径'], ['lecture', '课程讲义'], ['mindmap', '思维导图'],
  ['quiz', '练习题库'], ['code_case', '代码实操'], ['ppt_outline', 'PPT 大纲'],
  ['multimodal_resource', '动态流程图'],
]

const defaultAttribution: Record<string, string> = {
  learning_path: 'PlannerAgent',
  lecture: 'ResourceAgent',
  mindmap: 'MindMapAgent',
  quiz: 'QuizAgent',
  code_case: 'CodeAgent',
  ppt_outline: 'ResourceAgent',
  multimodal_resource: 'ResourceAgent',
}

const stageNames: Record<string, string> = {
  profile_loaded: '画像加载',
  knowledge_retrieved: '知识检索',
  plan_generated: '路径规划',
  resources_generated: '资源生成',
  quiz_generated: '测评生成',
  review_completed: '内容审校',
  saved: '保存完成',
}

export default function ResourcesPage() {
  const [topic, setTopic] = useState('Pandas 数据清洗与分析综合实践')
  const [profile, setProfile] = useState<Profile | null>(null)
  const [active, setActive] = useState('learning_path')
  const [resources, setResources] = useState<Record<string, any>>({})
  const [attribution, setAttribution] = useState<Record<string, string>>(defaultAttribution)
  const [citations, setCitations] = useState<Citation[]>([])
  const [workflow, setWorkflow] = useState<any[]>([])
  const [progress, setProgress] = useState(0)
  const [agent, setAgent] = useState('')
  const [stage, setStage] = useState('等待启动')
  const [review, setReview] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<Resource[]>([])
  const [resourceId, setResourceId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<number | null>(null)
  const [generation, setGeneration] = useState<Record<string, GenerationMeta>>({})
  const [error, setError] = useState('')
  const [plan, setPlan] = useState<LearningPlan | null>(null)

  const load = async () => {
    const [current, packs, activePlan] = await Promise.all([
      api<Profile | null>('/api/profiles'),
      api<Resource[]>('/api/resources'),
      api<LearningPlan | null>('/api/learning/tasks'),
    ])
    setProfile(current)
    setHistory(packs)
    setPlan(activePlan)
  }
  useEffect(() => { load().catch(() => null) }, [])

  const generate = async () => {
    setLoading(true); setResources({}); setCitations([]); setReview(null); setWorkflow([]); setGeneration({}); setError('')
    setProgress(1); setStage('启动总控流程')
    try {
      await consumeSSE('/api/resources/generate', { topic, profile_id: profile?.id }, (event, data) => {
        if (event === 'progress') {
          setProgress(data.progress); setAgent(data.agent); setStage(`${data.state} · ${data.description}`)
          setWorkflow(previous => [...previous.filter(item => item.state !== data.state), data])
        }
        if (event === 'citations') setCitations(data)
        if (event === 'resource') {
          setResources(previous => ({ ...previous, [data.type]: data.content }))
          setAttribution(previous => ({ ...previous, [data.type]: data.generated_by }))
          setGeneration(previous => ({ ...previous, [data.type]: data.generation || {} }))
        }
        if (event === 'review') setReview(data)
        if (event === 'done') {
          setResourceId(data.resource_id)
          setFeedback(null)
          setProgress(100); setStage(data.message); setWorkflow(data.workflow || [])
          api<LearningPlan>(`/api/learning/tasks?resource_id=${data.resource_id}`).then(setPlan).catch(() => null)
          load()
        }
      })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '资源生成失败')
    } finally {
      setLoading(false)
    }
  }

  const openHistory = (item: Resource) => {
    setTopic(item.topic)
    setResources(item.content)
    setCitations(item.content.citations || [])
    setWorkflow(item.content.workflow || [])
    setReview(item.review)
    setGeneration(item.content.generation_metadata || {})
    setResourceId(item.id)
    setFeedback(null)
    setProgress(100)
    setStage('已加载历史资源包')
    api<LearningPlan>(`/api/learning/tasks?resource_id=${item.id}`).then(setPlan).catch(() => null)
  }

  const content = resources[active]
  const activeMeta = generation[active] || {}
  const rateResource = async (rating: 1 | -1) => {
    if (!resourceId) return
    await api(`/api/resources/${resourceId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ rating }),
    })
    setFeedback(rating)
  }
  const toggleTask = async (taskId: number, completed: boolean) => {
    const updated = await api<LearningPlan>(`/api/learning/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ completed }),
    })
    setPlan(updated)
  }
  return (
    <>
      <PageHeader eyebrow="Multi-Agent Orchestrator" title="可追踪、可归因的多智能体资源生成" description="每个阶段、智能体输出和资源归属都会写入资源包。生成内容同时使用当前画像、知识库、历史薄弱点、主题和资源偏好。" />
      <Card className="mb-6">
        <div className="mb-4 flex flex-col gap-3 rounded-2xl bg-violet-50 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3"><UserRound className="text-violet-600" /><div><div className="text-xs text-violet-500">当前学习者</div><div className="font-black">{profile?.display_name || '未选择'} · {profile?.learning_style}</div></div></div>
          <Link to="/profile" className="text-xs font-bold text-violet-700">切换演示学生</Link>
        </div>
        <div className="flex flex-col gap-3 lg:flex-row">
          <input value={topic} onChange={event => setTopic(event.target.value)} className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-violet-400" />
          <Button loading={loading} disabled={!profile} onClick={generate} className="lg:min-w-44">启动智能体协作</Button>
        </div>
        {error && <div className="mt-3 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
        {(loading || progress > 0) && <div className="mt-5">
          <div className="mb-2 flex justify-between text-xs"><span className="font-bold text-violet-700">{agent || 'Orchestrator'} · {stage}</span><span>{progress}%</span></div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 transition-all duration-500" style={{ width: `${progress}%` }} /></div>
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
            {workflow.map((item, index) => <div key={item.state} className="min-w-32 shrink-0 rounded-2xl border border-violet-200 bg-violet-50 p-3 text-xs text-violet-700"><div className="flex items-center gap-2 font-black"><CheckCircle2 className="h-3.5 w-3.5" />{index + 1}. {stageNames[item.state] || item.state}</div><div className="mt-1 line-clamp-2 text-[10px] text-violet-500">{item.agent}</div></div>)}
            {workflow.length < 7 && <div className="flex shrink-0 items-center gap-2 rounded-full border border-slate-100 px-3 py-2 text-xs text-slate-400"><Circle className="h-3.5 w-3.5" />等待后续状态</div>}
          </div>
        </div>}
      </Card>
      <div className="grid gap-6 xl:grid-cols-[1fr_300px]">
        <Card className="min-w-0">
          <div className="flex gap-2 overflow-x-auto border-b border-slate-100 pb-4">
            {tabs.map(([key, label]) => <button key={key} onClick={() => setActive(key)} className={`shrink-0 rounded-xl px-3 py-2 text-xs font-bold ${active === key ? 'bg-slate-950 text-white' : 'bg-slate-50 text-slate-500'}`}>{label}</button>)}
          </div>
          <div className="mt-4 flex flex-wrap justify-end gap-2">
            <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">智能体：{attribution[active]}</span>
            <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-bold text-violet-700">{activeMeta.label || 'Mock 规则生成'}</span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">{activeMeta.rag_enhanced ? '已使用知识库证据' : '未使用知识库证据'}</span>
            <span className={`rounded-full px-3 py-1 text-xs font-bold ${!review ? 'bg-slate-100 text-slate-500' : review?.checks?.human_review_required ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>{!review ? '等待审校' : review?.checks?.human_review_required ? '需要人工核验' : '规则审校通过'}</span>
          </div>
          <div className="mt-4">
            {!content ? <EmptyState title="等待真实生成流程" text="选择学生并启动后，资源会随 SSE 事件逐项出现。" />
              : active === 'mindmap' ? <Mermaid chart={content} />
              : active === 'quiz' ? <div className="space-y-4">{content.map((question: any, index: number) => <div key={question.id} className="rounded-2xl bg-slate-50 p-4"><div className="text-xs font-bold text-violet-600">第 {index + 1} 题 · {question.knowledge_point}</div><div className="mt-2 font-bold">{question.question}</div>{question.options?.length > 0 && <div className="mt-2 grid gap-2 sm:grid-cols-2">{question.options.map((option: string) => <div key={option} className="rounded-xl bg-white px-3 py-2 text-sm">{option}</div>)}</div>}</div>)}</div>
              : active === 'multimodal_resource' ? <iframe title={content.title} srcDoc={content.html} sandbox="" className="h-[520px] w-full rounded-2xl border border-violet-100 bg-white" />
              : <Markdown>{String(content)}</Markdown>}
          </div>
          {resourceId && active === 'ppt_outline' && <a href={`http://localhost:8000/api/resources/${resourceId}/pptx`} className="mt-5 inline-flex items-center gap-2 rounded-2xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white"><Download className="h-4 w-4" />下载个性化 PPT 文件</a>}
        </Card>
        <div className="space-y-6">
          {plan && <Card>
            <div className="flex items-center gap-2"><Clock3 className="text-violet-600" /><h3 className="font-black">可执行学习计划</h3></div>
            <div className="mt-1 text-[11px] text-slate-500">{plan.topic}</div>
            <div className="mt-3 flex items-center justify-between text-xs"><span>{plan.completed}/{plan.total} 已完成</span><span className="font-bold text-violet-700">{plan.progress}% · 剩余约 {plan.remaining_minutes} 分钟</span></div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500" style={{ width: `${plan.progress}%` }} /></div>
            <div className="mt-4 space-y-2">{plan.tasks.map(task => <button key={task.id} onClick={() => toggleTask(task.id, task.status !== 'completed')} className={`w-full rounded-xl p-3 text-left ${task.status === 'completed' ? 'bg-emerald-50' : 'bg-slate-50 hover:bg-violet-50'}`}>
              <div className="flex gap-2">{task.status === 'completed' ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> : <Circle className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />}<div><div className="text-xs font-black">{task.title} · {task.estimated_minutes} 分钟</div><div className="mt-1 text-[11px] leading-5 text-slate-500">{task.description}</div></div></div>
            </button>)}</div>
          </Card>}
          {review && <Card>
            <div className="flex items-center gap-2"><ShieldCheck className={review.passed ? 'text-emerald-600' : 'text-amber-600'} /><h3 className="font-black">规则审校报告</h3></div>
            <div className="mt-4 flex items-end justify-between"><div className="text-4xl font-black">{review.score}<span className="text-sm text-slate-400"> / 100</span></div><span className={`rounded-full px-3 py-1 text-xs font-bold ${review.passed ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>{review.status}</span></div>
            {review.checks && <div className="mt-4 space-y-2">{Object.entries(review.checks).map(([name, passed]) => <div key={name} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-xs"><span>{name}</span><span className={passed && name !== 'human_review_required' ? 'text-emerald-600' : 'text-amber-600'}>{String(passed)}</span></div>)}</div>}
            {review.warnings?.map((warning: string) => <div key={warning} className="mt-2 rounded-xl bg-amber-50 p-2 text-xs text-amber-700">{warning}</div>)}
          </Card>}
          {resourceId && <Card>
            <h3 className="font-black">资源使用反馈</h3>
            <p className="mt-2 text-xs leading-5 text-slate-500">反馈真实写入学习记录，用于判断资源是否需要调整，不用于虚构“满意度”。</p>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button onClick={() => rateResource(1)} className={`flex items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-bold ${feedback === 1 ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-700'}`}><ThumbsUp className="h-4 w-4" />有帮助</button>
              <button onClick={() => rateResource(-1)} className={`flex items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-bold ${feedback === -1 ? 'bg-amber-600 text-white' : 'bg-amber-50 text-amber-700'}`}><ThumbsDown className="h-4 w-4" />需要调整</button>
            </div>
          </Card>}
          <Card>
            <div className="flex items-center gap-2"><GitBranch className="text-violet-600" /><h3 className="font-black">RAG 证据</h3></div>
            <div className="mt-3 space-y-2">{citations.slice(0, 4).map(citation => <div key={citation.chunk_id} className="rounded-xl bg-slate-50 p-3 text-xs"><div className="flex justify-between font-bold text-violet-600"><span>{citation.title}</span><span>{Math.round(citation.score * 100)}%</span></div><div className="mt-1 line-clamp-3 leading-5 text-slate-500">{citation.content}</div></div>)}</div>
          </Card>
          {history.length > 0 && <Card>
            <div className="flex items-center gap-2"><Bot className="text-indigo-600" /><h3 className="font-black">该生历史资源包</h3></div>
            <div className="mt-3 space-y-2">{history.slice(0, 4).map(item => <button key={item.id} onClick={() => openHistory(item)} className="w-full rounded-xl bg-slate-50 p-3 text-left text-xs hover:bg-violet-50"><div className="font-bold">{item.topic}</div><div className="mt-1 text-slate-400">{new Date(item.created_at).toLocaleString()}</div></button>)}</div>
          </Card>}
        </div>
      </div>
    </>
  )
}
