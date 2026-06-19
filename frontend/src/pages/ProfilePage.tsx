import { useEffect, useState } from 'react'
import { BrainCircuit, Check, Send, Users } from 'lucide-react'
import { api } from '../api'
import { Button, Card, EmptyState, PageHeader } from '../components'
import type { Profile } from '../types'

const example = '我是计算机专业大二学生，Python 基础一般，函数、Pandas 和数据分析项目不熟，希望通过图解、代码案例和项目练习学习。'

const fieldNames: Record<string, string> = {
  major: '专业',
  grade: '年级',
  knowledge_level: '知识基础',
  learning_goal: '学习目标',
  weak_points: '知识短板',
  learning_style: '学习风格',
  resource_preference: '资源偏好',
  mistake_history: '错题与薄弱记录',
}

export default function ProfilePage() {
  const [text, setText] = useState(example)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [changes, setChanges] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [generation, setGeneration] = useState<any>(null)

  const load = async () => {
    const [current, all] = await Promise.all([
      api<Profile | null>('/api/profiles'),
      api<Profile[]>('/api/profiles/all'),
    ])
    setProfile(current)
    setProfiles(all)
  }
  useEffect(() => { load().catch(() => null) }, [])

  const generate = async () => {
    setLoading(true); setError('')
    try {
      const result = await api<any>('/api/profiles', {
        method: 'POST',
        body: JSON.stringify({ text, display_name: '自定义学习者' }),
      })
      setProfile(result.profile)
      setChanges(result.changes || [])
      setGeneration(result.generation || null)
      await load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const selectProfile = async (id?: number) => {
    if (!id) return
    const selected = await api<Profile>('/api/profiles/select', {
      method: 'POST',
      body: JSON.stringify({ profile_id: id }),
    })
    setProfile(selected)
    setChanges([])
    setGeneration(null)
    await load()
  }

  const fields = profile ? [
    ['专业', profile.major], ['年级', profile.grade], ['知识基础', profile.knowledge_level],
    ['学习目标', profile.learning_goal], ['知识短板', profile.weak_points.join('、')],
    ['学习风格', profile.learning_style], ['资源偏好', profile.resource_preference.join('、')],
    ['错题与薄弱记录', profile.mistake_history.join('；') || '暂无，完成测评后动态更新'],
  ] : []

  return (
    <>
      <PageHeader
        eyebrow="Profile Agent"
        title="自然语言抽取，而不是固定画像模板"
        description="Mock 模式也会根据原文执行规则抽取并写入 SQLite。你可以切换三类演示学生，验证同一主题下的个性化差异。"
      />
      <Card className="mb-6">
        <div className="flex items-center gap-2"><Users className="h-5 w-5 text-violet-600" /><h3 className="font-black">演示学生与当前学习者</h3></div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {profiles.map(item => (
            <button key={item.id} onClick={() => selectProfile(item.id)} className={`rounded-2xl border p-4 text-left transition ${item.is_active ? 'border-violet-400 bg-violet-50 ring-4 ring-violet-100' : 'border-slate-100 bg-slate-50 hover:border-violet-200'}`}>
              <div className="flex items-center justify-between"><span className="font-black">{item.display_name}</span>{item.is_active && <Check className="h-4 w-4 text-violet-600" />}</div>
              <div className="mt-2 text-xs leading-5 text-slate-500">{item.knowledge_level} · {item.learning_style}</div>
              <div className="mt-2 text-[11px] text-violet-600">{item.demo_key ? '内置演示画像' : '自然语言生成画像'}</div>
            </button>
          ))}
        </div>
      </Card>
      <div className="grid gap-6 xl:grid-cols-[.85fr_1.15fr]">
        <Card className="h-fit">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-violet-100 text-violet-700"><BrainCircuit /></div>
            <div><div className="font-black">ProfileAgent</div><div className="text-xs text-slate-400">基于原文抽取八维画像</div></div>
          </div>
          <textarea value={text} onChange={event => setText(event.target.value)} className="min-h-52 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-7 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-100" />
          {error && <div className="mt-3 text-sm text-rose-600">{error}</div>}
          <Button loading={loading} onClick={generate} className="mt-4 w-full"><Send className="h-4 w-4" />生成并保存画像</Button>
          {generation && <div className={`mt-3 rounded-xl p-3 text-center text-xs font-bold ${generation.used_real_model ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-800'}`}>生成来源：{generation.label || 'Mock 规则生成'}{generation.fallback_used ? '（真实模型失败后已回退）' : ''}</div>}
          <p className="mt-3 text-center text-xs text-slate-400">当前状态：MVP 实现。无模型 Key 时使用输入驱动的规则抽取，不返回固定画像。</p>
        </Card>
        <div>
          {profile ? <>
            <div className="mb-3 flex items-center justify-between"><h3 className="font-black">{profile.display_name}的画像</h3><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">SQLite 已保存</span></div>
            <div className="grid gap-4 sm:grid-cols-2">
              {fields.map(([name, value], index) => <Card key={name} className={index === 3 || index === 7 ? 'sm:col-span-2' : ''}>
                <div className="text-xs font-bold text-violet-500">0{index + 1} · {name}</div>
                <div className="mt-2 text-sm font-semibold leading-6 text-slate-800">{value}</div>
              </Card>)}
            </div>
            {changes.length > 0 && <Card className="mt-4 border-emerald-100 bg-emerald-50/80">
              <h3 className="font-black text-emerald-800">本次画像变化</h3>
              <div className="mt-3 space-y-2">{changes.map(change => <div key={change.field} className="rounded-xl bg-white/80 p-3 text-xs"><span className="font-bold text-emerald-700">{fieldNames[change.field] || change.field}</span><div className="mt-1 text-slate-500">更新前：{Array.isArray(change.before) ? change.before.join('、') : String(change.before ?? '无')}</div><div className="mt-1 text-slate-800">更新后：{Array.isArray(change.after) ? change.after.join('、') : String(change.after ?? '无')}</div></div>)}</div>
            </Card>}
          </> : <EmptyState title="等待生成学习画像" text="输入学习情况，或选择一个内置演示学生。" />}
        </div>
      </div>
    </>
  )
}
