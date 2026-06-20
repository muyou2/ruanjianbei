import { useEffect, useState } from 'react'
import { Activity, ArrowRight, BookMarked, BrainCircuit, ChartNoAxesCombined, CheckCircle2, Circle, Clock3, Cpu, Files } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Card, PageHeader } from '../components'
import type { LearningPlan, Profile, Resource } from '../types'

export default function Dashboard() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [resources, setResources] = useState<Resource[]>([])
  const [signals, setSignals] = useState<any>(null)
  const [config, setConfig] = useState<any>(null)
  const [testingModel, setTestingModel] = useState(false)
  const [modelError, setModelError] = useState('')
  const [plan, setPlan] = useState<LearningPlan | null>(null)

  useEffect(() => {
    Promise.all([
      api<Profile | null>('/api/profiles'),
      api<any[]>('/api/documents'),
      api<Resource[]>('/api/resources'),
      api<any>('/api/analytics/overview'),
      api<any>('/api/config/status'),
    ]).then(([current, docs, packs, analytics, configStatus]) => {
      setProfile(current)
      setDocuments(docs)
      setResources(packs)
      setSignals(analytics.personal_signals)
      setPlan(analytics.personal_signals?.active_plan || null)
      setConfig(configStatus)
    }).catch(() => null)
  }, [])

  const testModel = async () => {
    setTestingModel(true); setModelError('')
    try {
      const result = await api<any>('/api/config/llm-test')
      setConfig((previous: any) => ({ ...previous, last_llm_test: result }))
    } catch (error) {
      setModelError(error instanceof Error ? error.message : '模型测试失败')
    } finally {
      setTestingModel(false)
    }
  }

  const toggleTask = async (taskId: number, completed: boolean) => {
    const updated = await api<LearningPlan>(`/api/learning/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ completed }),
    })
    setPlan(updated)
    setSignals((previous: any) => ({ ...previous, active_plan: updated }))
  }

  const latestScore = signals?.latest_evaluation?.score
  const mastery = signals?.mastery || []
  const eventLabel: Record<string, string> = {
    created: '创建学生画像',
    generated: '生成资源包',
    asked: '向智能助教提问',
    completed: '完成学习评估',
    rated: '评价学习资源',
    progressed: '推进学习任务',
  }
  const stats = [
    { label: '当前画像', value: profile ? '8 维' : '未创建', icon: BrainCircuit, color: 'from-violet-500 to-fuchsia-500' },
    { label: '课程资料', value: `${documents.length} 份`, icon: Files, color: 'from-blue-500 to-cyan-500' },
    { label: '该生资源包', value: `${resources.length} 个`, icon: BookMarked, color: 'from-amber-500 to-orange-500' },
    { label: '最近测评', value: latestScore == null ? '待完成' : `${latestScore} 分`, icon: ChartNoAxesCombined, color: 'from-emerald-500 to-teal-500' },
  ]

  return (
    <>
      <PageHeader eyebrow="Dashboard" title="当前学生的真实学习闭环" description="面向高校 Python 课程的个性化 AI 学习智能体平台。这里只展示当前学生真实产生的画像、资源、测评和学习轨迹。" />
      <div className="mb-6 flex gap-2 overflow-x-auto pb-1">
        {['了解学生', '检索知识', '生成资源', '智能辅导', '学习评估', '动态调整'].map((item, index) => <div key={item} className="flex shrink-0 items-center gap-2"><span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-2 text-xs font-black text-violet-700">{index + 1}. {item}</span>{index < 5 && <span className="text-violet-300">→</span>}</div>)}
      </div>
      <Card className="mb-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3"><Cpu className="mt-1 text-violet-600" /><div><h3 className="font-black">模型与检索验收状态</h3><div className="mt-2 flex flex-wrap gap-2 text-xs"><span className="rounded-full bg-slate-100 px-3 py-1">Provider：{config?.provider || '加载中'}</span><span className="rounded-full bg-slate-100 px-3 py-1">模型：{config?.model || '加载中'}</span><span className={`rounded-full px-3 py-1 ${config?.mock_mode ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>{config?.configuration_error ? '配置异常，调用时回退 Mock' : config?.mock_mode ? '当前为 Mock 模式' : '真实模型已配置'}</span><span className="rounded-full bg-violet-50 px-3 py-1 text-violet-700">{config?.retrieval?.mode || '检索加载中'}</span></div></div></div>
          <button disabled={testingModel} onClick={testModel} className="rounded-xl bg-slate-950 px-4 py-2 text-xs font-bold text-white disabled:opacity-50">{testingModel ? '正在测试模型…' : '测试当前模型连接'}</button>
        </div>
        {config?.configuration_error && <div className="mt-3 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{config.configuration_error}</div>}
        {modelError && <div className="mt-3 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{modelError}</div>}
        {config?.last_llm_test && <div className={`mt-3 rounded-xl p-3 text-xs ${config.last_llm_test.success && !config.last_llm_test.fallback_used ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-800'}`}><b>最近测试：</b>{config.last_llm_test.success ? '请求完成' : '真实模型未通过'} · fallback={String(config.last_llm_test.fallback_used)} · {config.last_llm_test.response_preview}{config.last_llm_test.error_message ? ` · ${config.last_llm_test.error_message}` : ''}</div>}
      </Card>
      <Card className="relative overflow-hidden !bg-slate-950 text-white">
        <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full bg-violet-500/30 blur-3xl" />
        <div className="relative max-w-3xl py-4 lg:py-8">
          <span className="rounded-full bg-violet-400/15 px-3 py-1 text-xs font-bold text-violet-200">中国软件杯 · 高校 Python 个性化学习</span>
          <h2 className="mt-5 text-3xl font-black leading-tight lg:text-5xl">{profile?.display_name || '当前学习者'}，<br /><span className="text-violet-300">下一步由学习证据决定。</span></h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">自然语言画像 → 知识库检索 → 多智能体资源 → RAG 答疑 → 测评 → 薄弱点写回画像。</p>
          <Link to={profile ? '/resources' : '/profile'} className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-3 text-sm font-bold text-slate-950">
            {profile ? '继续本次学习' : '创建学习画像'}<ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </Card>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, color }) => <Card key={label}>
          <div className={`grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br ${color} text-white`}><Icon className="h-5 w-5" /></div>
          <div className="mt-4 text-2xl font-black">{value}</div><div className="text-sm text-slate-500">{label}</div>
        </Card>)}
      </div>
      <Card className="mt-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2"><Clock3 className="h-5 w-5 text-violet-600" /><h3 className="font-black">当前可执行学习计划</h3></div>
            <p className="mt-1 text-xs text-slate-500">{plan ? `${plan.topic} · 剩余约 ${plan.remaining_minutes} 分钟` : '生成资源包后，系统会把学习路径转成可执行任务。'}</p>
          </div>
          {plan && <div className="min-w-44">
            <div className="mb-1 flex justify-between text-xs font-bold"><span>{plan.completed}/{plan.total} 已完成</span><span>{plan.progress}%</span></div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500" style={{ width: `${plan.progress}%` }} /></div>
          </div>}
        </div>
        {plan ? <div className="mt-4 grid gap-2 md:grid-cols-5">
          {plan.tasks.map(task => <button key={task.id} onClick={() => toggleTask(task.id, task.status !== 'completed')} className={`rounded-2xl border p-3 text-left transition ${task.status === 'completed' ? 'border-emerald-200 bg-emerald-50' : 'border-slate-100 bg-slate-50 hover:border-violet-200'}`}>
            <div className="flex items-start gap-2">{task.status === 'completed' ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> : <Circle className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />}<div><div className="text-xs font-black">{task.title}</div><div className="mt-1 text-[11px] text-slate-500">约 {task.estimated_minutes} 分钟</div></div></div>
          </button>)}
        </div> : <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">暂无计划。先到资源中心生成一个学习主题。</div>}
      </Card>
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
        <Card>
          <div className="flex items-center justify-between"><h3 className="font-black">当前画像与动态薄弱点</h3><Link to="/profile" className="text-xs font-bold text-violet-600">切换或查看画像</Link></div>
          {profile && <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-slate-50 p-4"><div className="text-xs font-bold text-slate-400">专业与年级</div><div className="mt-1 text-sm font-semibold">{profile.major} · {profile.grade}</div></div>
            <div className="rounded-2xl bg-slate-50 p-4"><div className="text-xs font-bold text-slate-400">学习类型</div><div className="mt-1 text-sm font-semibold">{profile.learning_style}</div></div>
            <div className="rounded-2xl bg-rose-50 p-4 sm:col-span-2"><div className="text-xs font-bold text-rose-500">当前薄弱点</div><div className="mt-2 flex flex-wrap gap-2">{profile.weak_points.map(item => <span key={item} className="rounded-full bg-white px-3 py-1 text-xs font-bold text-rose-700">{item}</span>)}</div></div>
          </div>}
          <div className="mt-4 rounded-2xl bg-gradient-to-r from-violet-50 to-indigo-50 p-4 text-sm leading-6 text-slate-700"><span className="font-black text-violet-700">系统建议：</span>{signals?.recommendation || '先生成画像并完成一次诊断测评。'}</div>
        </Card>
        <Card>
          <h3 className="font-black">最近错题与测评证据</h3>
          {profile?.mistake_history?.length ? <div className="mt-4 space-y-2">{profile.mistake_history.slice(-5).reverse().map((item, index) => <div key={`${item}-${index}`} className="rounded-2xl bg-amber-50 p-3 text-sm leading-6 text-amber-900">{item}</div>)}</div>
            : <div className="mt-4 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">暂无错题记录。完成学习评估后，对应知识点会写回这里。</div>}
          {signals?.latest_evaluation && <div className="mt-4 border-t border-slate-100 pt-4 text-xs leading-6 text-slate-500">最近测评：{signals.latest_evaluation.score} 分<br />识别薄弱点：{signals.latest_evaluation.weak_points.join('、') || '无'}</div>}
        </Card>
      </div>
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
        <Card>
          <div className="flex items-center justify-between"><h3 className="font-black">知识点掌握度</h3><span className="text-xs text-slate-400">基于真实逐题得分滚动计算</span></div>
          <div className="mt-4 space-y-4">
            {mastery.slice(0, 6).map((item: any) => <div key={item.knowledge_point}>
              <div className="mb-1.5 flex justify-between text-xs"><span className="font-bold">{item.knowledge_point}</span><span className={item.mastery < 60 ? 'text-rose-600' : 'text-emerald-600'}>{item.mastery}% · {item.attempts} 次</span></div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${item.mastery < 60 ? 'bg-gradient-to-r from-rose-400 to-orange-400' : 'bg-gradient-to-r from-emerald-400 to-teal-500'}`} style={{ width: `${item.mastery}%` }} /></div>
            </div>)}
            {!mastery.length && <div className="rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">完成一次测评后，这里会形成按知识点拆分的掌握度，而不只显示总分。</div>}
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-2"><Activity className="h-4 w-4 text-violet-600" /><h3 className="font-black">近期学习轨迹</h3></div>
          <div className="mt-4 space-y-3">
            {(signals?.recent_events || []).slice(0, 6).map((item: any) => <div key={item.id} className="flex gap-3 rounded-2xl bg-slate-50 p-3">
              <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-violet-500" />
              <div><div className="text-sm font-bold">{eventLabel[item.verb] || item.verb}</div><div className="mt-1 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</div></div>
            </div>)}
            {!signals?.recent_events?.length && <div className="text-sm text-slate-500">尚无学习行为记录。</div>}
          </div>
          <div className="mt-4 rounded-2xl bg-violet-50 p-3 text-xs text-violet-700">资源反馈：有帮助 {signals?.resource_feedback?.helpful || 0} 次，需要调整 {signals?.resource_feedback?.needs_adjustment || 0} 次。</div>
        </Card>
      </div>
      <Card className="mt-6">
        <div className="flex items-center justify-between"><h3 className="font-black">当前学生的资源生成历史</h3><Link to="/resources" className="text-xs font-bold text-violet-600">进入资源中心</Link></div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {resources.slice(0, 6).map(item => <div key={item.id} className="rounded-2xl bg-slate-50 p-4"><div className="font-bold">{item.topic}</div><div className="mt-2 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()} · 审校 {item.review?.status || item.review?.score}</div></div>)}
          {!resources.length && <div className="text-sm text-slate-500">当前学生尚未生成资源包。</div>}
        </div>
      </Card>
    </>
  )
}
