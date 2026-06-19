import { useEffect, useState } from 'react'
import { Bot, CheckCircle2, Circle, GitBranch, ShieldCheck } from 'lucide-react'
import { api, consumeSSE } from '../api'
import { Button, Card, EmptyState, Markdown, Mermaid, PageHeader } from '../components'
import type { Citation, Resource } from '../types'

const tabs = [
  ['learning_path', '学习路径'], ['lecture', '课程讲义'], ['mindmap', '思维导图'],
  ['quiz', '练习题库'], ['code_case', '代码实操'], ['ppt_outline', 'PPT 大纲'],
]
const agents = ['知识检索员', '路径规划师', '课程讲义师', '测评设计师', '代码教练', '知识图谱师', '事实审校员']

export default function ResourcesPage() {
  const [topic, setTopic] = useState('Python 数据分析综合实践')
  const [active, setActive] = useState('learning_path')
  const [resources, setResources] = useState<Record<string, any>>({})
  const [citations, setCitations] = useState<Citation[]>([])
  const [progress, setProgress] = useState(0)
  const [agent, setAgent] = useState('')
  const [stage, setStage] = useState('等待启动')
  const [review, setReview] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<Resource[]>([])
  const loadHistory = () => api<Resource[]>('/api/resources').then(setHistory)
  useEffect(() => { loadHistory().catch(() => null) }, [])
  const generate = async () => {
    setLoading(true); setResources({}); setCitations([]); setReview(null); setProgress(1); setStage('正在唤醒智能体')
    try {
      await consumeSSE('/api/resources/generate', { topic }, (event, data) => {
        if (event === 'progress') { setProgress(data.progress); setAgent(data.agent); setStage(data.stage) }
        if (event === 'citations') setCitations(data)
        if (event === 'resource') setResources(prev => ({ ...prev, [data.type]: data.content }))
        if (event === 'review') setReview(data)
        if (event === 'done') { setProgress(100); setStage(data.message); loadHistory() }
      })
    } finally { setLoading(false) }
  }
  const openHistory = (item: Resource) => { setTopic(item.topic); setResources(item.content); setCitations(item.content.citations || []); setReview(item.review); setProgress(100); setStage('已加载历史资源包') }
  const content = resources[active]
  return (
    <>
      <PageHeader eyebrow="Multi-Agent Orchestrator" title="一键生成完整个性化学习资源包" description="总控智能体依次检索知识、规划路径，并行生成六类资源，最后由事实审校员检查引用覆盖与风险。" />
      <Card className="mb-6">
        <div className="flex flex-col gap-3 lg:flex-row">
          <input value={topic} onChange={e => setTopic(e.target.value)} className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-violet-400" placeholder="输入本次学习主题" />
          <Button loading={loading} onClick={generate} className="lg:min-w-44">启动智能体协作</Button>
        </div>
        {(loading || progress > 0) && <div className="mt-5">
          <div className="mb-2 flex justify-between text-xs"><span className="font-bold text-violet-700">{agent || '总控智能体'} · {stage}</span><span>{progress}%</span></div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 transition-all duration-500" style={{ width: `${progress}%` }} /></div>
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
            {agents.map((name, i) => <div key={name} className={`flex shrink-0 items-center gap-2 rounded-full border px-3 py-2 text-xs font-bold ${agent === name || progress >= (i + 1) * 13 ? 'border-violet-200 bg-violet-50 text-violet-700' : 'border-slate-100 text-slate-400'}`}>
              {progress >= (i + 1) * 13 ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}{name}
            </div>)}
          </div>
        </div>}
      </Card>
      <div className="grid gap-6 xl:grid-cols-[1fr_280px]">
        <Card className="min-w-0">
          <div className="flex gap-2 overflow-x-auto border-b border-slate-100 pb-4">
            {tabs.map(([key, label]) => <button key={key} onClick={() => setActive(key)} className={`shrink-0 rounded-xl px-3 py-2 text-xs font-bold ${active === key ? 'bg-slate-950 text-white' : 'bg-slate-50 text-slate-500'}`}>{label}</button>)}
          </div>
          <div className="mt-5">
            {!content ? <EmptyState title="资源正在等待生成" text="输入学习主题并启动智能体协作。" />
              : active === 'mindmap' ? <Mermaid chart={content} />
              : active === 'quiz' ? <div className="space-y-4">{content.map((q: any, i: number) => <div key={q.id} className="rounded-2xl bg-slate-50 p-4"><div className="text-xs font-bold text-violet-600">第 {i + 1} 题 · {q.knowledge_point}</div><div className="mt-2 font-bold">{q.question}</div>{q.options?.length > 0 && <div className="mt-2 grid gap-2 sm:grid-cols-2">{q.options.map((o: string) => <div key={o} className="rounded-xl bg-white px-3 py-2 text-sm">{o}</div>)}</div>}</div>)}</div>
              : <Markdown>{String(content)}</Markdown>}
          </div>
        </Card>
        <div className="space-y-6">
          {review && <Card>
            <div className="flex items-center gap-2"><ShieldCheck className="text-emerald-600" /><h3 className="font-black">审校报告</h3></div>
            <div className="mt-4 text-4xl font-black text-emerald-600">{review.score}<span className="text-sm text-slate-400"> / 100</span></div>
            <div className="mt-3 text-xs leading-6 text-slate-500">引用 {review.citation_count} 条 · 安全检查{review.safety}<br />{review.note}</div>
            {review.dimensions && <div className="mt-4 space-y-2">{Object.entries(review.dimensions).map(([name, value]) => <div key={name}><div className="mb-1 flex justify-between text-[11px]"><span>{name}</span><span className="font-bold">{String(value)}</span></div><div className="h-1.5 rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-500" style={{ width: `${value}%` }} /></div></div>)}</div>}
            {review.warnings?.map((w: string) => <div key={w} className="mt-2 rounded-xl bg-amber-50 p-2 text-xs text-amber-700">{w}</div>)}
          </Card>}
          <Card>
            <div className="flex items-center gap-2"><GitBranch className="text-violet-600" /><h3 className="font-black">知识引用</h3></div>
            <div className="mt-3 space-y-2">{citations.slice(0, 4).map(c => <div key={c.chunk_id} className="rounded-xl bg-slate-50 p-3 text-xs"><div className="font-bold text-violet-600">{c.title}</div><div className="mt-1 line-clamp-3 leading-5 text-slate-500">{c.content}</div></div>)}</div>
          </Card>
          {history.length > 0 && <Card>
            <div className="flex items-center gap-2"><Bot className="text-indigo-600" /><h3 className="font-black">历史资源包</h3></div>
            <div className="mt-3 space-y-2">{history.slice(0, 4).map(item => <button key={item.id} onClick={() => openHistory(item)} className="w-full rounded-xl bg-slate-50 p-3 text-left text-xs hover:bg-violet-50"><div className="font-bold">{item.topic}</div><div className="mt-1 text-slate-400">{new Date(item.created_at).toLocaleString()}</div></button>)}</div>
          </Card>}
        </div>
      </div>
    </>
  )
}
