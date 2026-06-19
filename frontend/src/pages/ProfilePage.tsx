import { useEffect, useState } from 'react'
import { BrainCircuit, Send } from 'lucide-react'
import { api } from '../api'
import { Button, Card, EmptyState, PageHeader } from '../components'
import type { Profile } from '../types'

const example = '我是电子信息专业大二学生，刚开始系统学习 Python，函数、面向对象和 Pandas 数据处理不太熟，希望通过图解、代码案例和项目练习掌握数据分析。'

export default function ProfilePage() {
  const [text, setText] = useState(example)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { api<Profile | null>('/api/profiles').then(setProfile).catch(() => null) }, [])
  const generate = async () => {
    setLoading(true); setError('')
    try { setProfile(await api('/api/profiles', { method: 'POST', body: JSON.stringify({ text }) })) }
    catch (e) { setError((e as Error).message) } finally { setLoading(false) }
  }
  const fields = profile ? [
    ['专业', profile.major], ['年级', profile.grade], ['知识基础', profile.knowledge_level],
    ['学习目标', profile.learning_goal], ['知识短板', profile.weak_points.join('、')],
    ['学习风格', profile.learning_style], ['资源偏好', profile.resource_preference.join('、')],
    ['错题与薄弱记录', profile.mistake_history.join('；') || '暂无，完成测评后动态更新'],
  ] : []
  return (
    <>
      <PageHeader eyebrow="Profile Agent" title="用一段对话，建立八维学习画像" description="无需填写冗长表单。画像分析师会理解专业、基础、目标、薄弱点与偏好，并在后续测评中持续更新。" />
      <div className="grid gap-6 xl:grid-cols-[.85fr_1.15fr]">
        <Card className="h-fit">
          <div className="mb-4 flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-2xl bg-violet-100 text-violet-700"><BrainCircuit /></div><div><div className="font-black">画像分析师</div><div className="text-xs text-slate-400">请自然地介绍你的学习情况</div></div></div>
          <textarea value={text} onChange={e => setText(e.target.value)} className="min-h-52 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-7 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-100" />
          {error && <div className="mt-3 text-sm text-rose-600">{error}</div>}
          <Button loading={loading} onClick={generate} className="mt-4 w-full"><Send className="h-4 w-4" />生成学习画像</Button>
          <p className="mt-3 text-center text-xs text-slate-400">没有模型 Key 时将使用本地规则与 Mock 数据生成</p>
        </Card>
        <div>
          {profile ? <>
            <div className="mb-3 flex items-center justify-between"><h3 className="font-black">我的画像卡片</h3><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">已动态保存</span></div>
            <div className="grid gap-4 sm:grid-cols-2">
              {fields.map(([name, value], i) => <Card key={name} className={i === 3 || i === 7 ? 'sm:col-span-2' : ''}>
                <div className="text-xs font-bold text-violet-500">0{i + 1} · {name}</div><div className="mt-2 text-sm font-semibold leading-6 text-slate-800">{value}</div>
              </Card>)}
            </div>
          </> : <EmptyState title="等待生成学习画像" text="左侧输入学习情况后，八个维度将在这里呈现。" />}
        </div>
      </div>
    </>
  )
}
