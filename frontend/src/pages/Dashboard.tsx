import { useEffect, useState } from 'react'
import { ArrowRight, BookMarked, BrainCircuit, CircleGauge, Files } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Card, PageHeader } from '../components'
import type { Profile, Resource } from '../types'

export default function Dashboard() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [resources, setResources] = useState<Resource[]>([])
  useEffect(() => {
    Promise.all([api<Profile | null>('/api/profiles'), api<any[]>('/api/documents'), api<Resource[]>('/api/resources')])
      .then(([p, d, r]) => { setProfile(p); setDocuments(d); setResources(r) }).catch(() => null)
  }, [])
  const stats = [
    { label: '画像维度', value: profile ? '8' : '0', icon: BrainCircuit, color: 'from-violet-500 to-fuchsia-500' },
    { label: '知识文档', value: String(documents.length), icon: Files, color: 'from-blue-500 to-cyan-500' },
    { label: '资源包', value: String(resources.length), icon: BookMarked, color: 'from-amber-500 to-orange-500' },
    { label: '学习闭环', value: 'RAG', icon: CircleGauge, color: 'from-emerald-500 to-teal-500' },
  ]
  return (
    <>
      <PageHeader eyebrow="Dashboard" title="今天，和一组 AI 教练一起学习" description="从自然语言画像出发，让八个专业智能体围绕 Python 课程协作生成、辅导、评估与持续优化。" />
      <Card className="relative overflow-hidden !bg-slate-950 text-white">
        <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full bg-violet-500/30 blur-3xl" />
        <div className="relative max-w-3xl py-4 lg:py-8">
          <span className="rounded-full bg-violet-400/15 px-3 py-1 text-xs font-bold text-violet-200">中国软件杯 · 个性化学习多智能体系统</span>
          <h2 className="mt-5 text-3xl font-black leading-tight lg:text-5xl">你的学习路径，<br /><span className="text-violet-300">应该像你一样独特。</span></h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">画像分析、课程检索、内容生成、事实审校与学习评估形成完整闭环。每一步都有来源、有进度、可解释。</p>
          <Link to={profile ? '/resources' : '/profile'} className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-3 text-sm font-bold text-slate-950">
            {profile ? '生成本次学习资源' : '创建我的学习画像'}<ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </Card>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, color }) => <Card key={label}>
          <div className={`grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br ${color} text-white`}><Icon className="h-5 w-5" /></div>
          <div className="mt-4 text-3xl font-black">{value}</div><div className="text-sm text-slate-500">{label}</div>
        </Card>)}
      </div>
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_.8fr]">
        <Card>
          <div className="flex items-center justify-between"><h3 className="font-black">当前学习画像</h3><Link to="/profile" className="text-xs font-bold text-violet-600">查看详情</Link></div>
          {profile ? <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {[['专业与年级', `${profile.major} · ${profile.grade}`], ['知识基础', profile.knowledge_level], ['学习风格', profile.learning_style], ['当前目标', profile.learning_goal]].map(([k, v]) =>
              <div key={k} className="rounded-2xl bg-slate-50 p-4"><div className="text-xs font-bold text-slate-400">{k}</div><div className="mt-1 text-sm font-semibold text-slate-800">{v}</div></div>)}
          </div> : <div className="mt-5 rounded-2xl bg-violet-50 p-5 text-sm text-violet-800">尚未生成画像。用一句自然语言介绍自己即可开始。</div>}
        </Card>
        <Card>
          <h3 className="font-black">智能体协作小队</h3>
          <div className="mt-4 grid grid-cols-4 gap-3">
            {['画像', '知识', '规划', '讲义', '测评', '代码', '导图', '审校'].map((name, i) =>
              <div key={name} className="text-center"><div className="mx-auto grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-violet-100 to-indigo-100 text-sm font-black text-violet-700">{i + 1}</div><div className="mt-1 text-[11px] text-slate-500">{name}</div></div>)}
          </div>
        </Card>
      </div>
    </>
  )
}
