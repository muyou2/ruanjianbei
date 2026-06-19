import { useState } from 'react'
import { BookOpenCheck, Send } from 'lucide-react'
import { consumeSSE } from '../api'
import { Button, Card, Markdown, PageHeader } from '../components'
import type { Citation } from '../types'

type Message = { role: 'user' | 'assistant'; content: string; citations?: Citation[] }

export default function TutorPage() {
  const [question, setQuestion] = useState('Python 中列表推导式和普通 for 循环应该如何选择？')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const ask = async () => {
    const q = question.trim(); if (!q || loading) return
    setQuestion(''); setLoading(true)
    setMessages(prev => [...prev, { role: 'user', content: q }, { role: 'assistant', content: '', citations: [] }])
    try {
      await consumeSSE('/api/tutor/chat', { question: q }, (event, data) => {
        setMessages(prev => {
          const next = [...prev]; const last = { ...next[next.length - 1] }
          if (event === 'citations') last.citations = data
          if (event === 'delta') last.content += data.text
          next[next.length - 1] = last; return next
        })
      })
    } finally { setLoading(false) }
  }
  return (
    <>
      <PageHeader eyebrow="RAG Tutor" title="有依据的即时答疑，而不是凭空作答" description="助教先检索课程知识库，再组织回答。每次回答都会展示参考片段与相关度，证据不足时明确提示。" />
      <Card className="mx-auto max-w-5xl p-0">
        <div className="flex min-h-[60vh] flex-col">
          <div className="border-b border-slate-100 p-5"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-500 text-white"><BookOpenCheck /></div><div><div className="font-black">Python 课程智能助教</div><div className="text-xs text-emerald-600">● 知识库已连接</div></div></div></div>
          <div className="flex-1 space-y-5 p-5 lg:p-7">
            {messages.length === 0 && <div className="mx-auto max-w-xl py-16 text-center"><div className="text-4xl">💬</div><h3 className="mt-3 font-black">从一个真实问题开始</h3><p className="mt-2 text-sm leading-6 text-slate-500">例如：如何理解函数参数？Pandas 如何处理缺失值？为什么我的循环结果不符合预期？</p></div>}
            {messages.map((message, i) => <div key={i} className={message.role === 'user' ? 'ml-auto max-w-2xl' : 'max-w-3xl'}>
              <div className={message.role === 'user' ? 'rounded-3xl rounded-br-md bg-slate-950 px-5 py-4 text-sm text-white' : 'rounded-3xl rounded-bl-md bg-violet-50 px-5 py-4'}>
                {message.role === 'assistant' ? (message.content ? <Markdown>{message.content}</Markdown> : <span className="animate-pulse text-sm text-violet-600">正在检索资料并组织回答…</span>) : message.content}
              </div>
              {message.citations && message.citations.length > 0 && <div className="mt-3 grid gap-2 sm:grid-cols-2">{message.citations.map((c, n) => <div key={c.chunk_id} className="rounded-2xl border border-slate-100 p-3 text-xs"><div className="flex justify-between font-bold text-violet-600"><span>参考 {n + 1} · {c.title}</span><span>{Math.round(c.score * 100)}%</span></div><p className="mt-1 line-clamp-3 leading-5 text-slate-500">{c.content}</p></div>)}</div>}
            </div>)}
          </div>
          <div className="border-t border-slate-100 p-4"><div className="flex gap-2"><textarea value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask() } }} className="min-h-12 flex-1 resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-violet-400" placeholder="输入课程问题，Enter 发送…" /><Button loading={loading} onClick={ask}><Send className="h-4 w-4" />发送</Button></div></div>
        </div>
      </Card>
    </>
  )
}
