import { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import {
  BookOpen, Bot, Boxes, BrainCircuit, ChartNoAxesCombined, Database,
  GraduationCap, LayoutDashboard, Menu, X,
} from 'lucide-react'
import { api } from './api'
import Dashboard from './pages/Dashboard'
import ProfilePage from './pages/ProfilePage'
import KnowledgePage from './pages/KnowledgePage'
import ResourcesPage from './pages/ResourcesPage'
import TutorPage from './pages/TutorPage'
import EvaluationPage from './pages/EvaluationPage'

const nav = [
  { to: '/', label: '学习总览', icon: LayoutDashboard },
  { to: '/profile', label: '学生画像', icon: BrainCircuit },
  { to: '/knowledge', label: '课程知识库', icon: Database },
  { to: '/resources', label: '资源生成', icon: Boxes },
  { to: '/tutor', label: '智能答疑', icon: Bot },
  { to: '/evaluation', label: '学习评估', icon: ChartNoAxesCombined },
]

export default function App() {
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState<any>(null)
  useEffect(() => { api('/api/config/status').then(setStatus).catch(() => null) }, [])
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <button onClick={() => setOpen(true)} className="fixed left-4 top-4 z-30 rounded-xl bg-slate-900 p-2 text-white lg:hidden"><Menu /></button>
      {open && <button aria-label="关闭菜单" onClick={() => setOpen(false)} className="fixed inset-0 z-30 bg-slate-950/30 lg:hidden" />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col bg-slate-950 px-4 py-5 text-white transition-transform lg:sticky lg:top-0 lg:h-screen ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-500"><GraduationCap /></div>
            <div><div className="font-black tracking-wide">智学方舟</div><div className="text-[10px] tracking-[.2em] text-violet-300">AGENTIC LEARNING</div></div>
          </div>
          <button onClick={() => setOpen(false)} className="lg:hidden"><X /></button>
        </div>
        <div className="mt-8 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)} end={to === '/'} className={({ isActive }) =>
              `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition ${isActive ? 'bg-white text-slate-950 shadow-lg' : 'text-slate-300 hover:bg-white/10 hover:text-white'}`}>
              <Icon className="h-4 w-4" />{label}
            </NavLink>
          ))}
        </div>
        <div className="mt-auto rounded-3xl border border-white/10 bg-white/5 p-4">
          <div className="flex items-center gap-2 text-xs font-bold"><span className={`h-2 w-2 rounded-full ${status ? 'bg-emerald-400' : 'bg-amber-400'}`} />系统状态</div>
          <div className="mt-3 text-xs leading-6 text-slate-400">
            <div>模型：{status?.mock_mode ? 'Mock 演示模式' : status?.provider || '连接中'}</div>
            <div>检索：{status?.vector_backend || '初始化中'}</div>
          </div>
        </div>
      </aside>
      <main className="min-w-0 px-5 pb-12 pt-20 lg:px-10 lg:pt-10 xl:px-14">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/resources" element={<ResourcesPage />} />
          <Route path="/tutor" element={<TutorPage />} />
          <Route path="/evaluation" element={<EvaluationPage />} />
        </Routes>
      </main>
    </div>
  )
}
