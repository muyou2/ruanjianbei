import { useEffect, useRef, useState } from 'react'
import { FileText, Search, UploadCloud, X } from 'lucide-react'
import { api } from '../api'
import { Button, Card, EmptyState, PageHeader } from '../components'
import type { Citation } from '../types'

export default function KnowledgePage() {
  const fileRef = useRef<HTMLInputElement>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [query, setQuery] = useState('Python 函数如何帮助组织数据分析代码？')
  const [results, setResults] = useState<Citation[]>([])
  const [loading, setLoading] = useState(false)
  const load = () => api<any[]>('/api/documents').then(setDocuments)
  useEffect(() => { load().catch(() => null) }, [])
  const upload = async (file?: File) => {
    if (!file) return
    setLoading(true)
    const form = new FormData(); form.append('file', file)
    try { await api('/api/documents', { method: 'POST', body: form }); await load() } finally { setLoading(false) }
  }
  const search = async () => setResults(await api('/api/knowledge/search', { method: 'POST', body: JSON.stringify({ query, top_k: 4 }) }))
  const remove = async (id: number) => { await api(`/api/documents/${id}`, { method: 'DELETE' }); await load() }
  return (
    <>
      <PageHeader eyebrow="Knowledge Agent" title="让每一次生成，都有课程资料作为锚点" description="上传 TXT、Markdown 或可提取文本的 PDF。系统自动切块、向量化并在生成与答疑时展示引用。" />
      <div className="grid gap-6 xl:grid-cols-[.9fr_1.1fr]">
        <div className="space-y-6">
          <Card>
            <button onClick={() => fileRef.current?.click()} className="grid min-h-48 w-full place-items-center rounded-3xl border-2 border-dashed border-violet-200 bg-violet-50/60 p-6 text-center transition hover:border-violet-400">
              <div><UploadCloud className="mx-auto h-9 w-9 text-violet-500" /><div className="mt-3 font-black">点击上传课程资料</div><div className="mt-1 text-xs text-slate-400">支持 .txt / .md / .pdf</div></div>
            </button>
            <input ref={fileRef} hidden type="file" accept=".txt,.md,.pdf" onChange={e => upload(e.target.files?.[0])} />
            {loading && <div className="mt-3 text-center text-sm text-violet-600">正在解析、切分并写入知识库…</div>}
          </Card>
          <Card>
            <h3 className="font-black">已入库文档 <span className="ml-2 text-xs text-slate-400">{documents.length} 份</span></h3>
            <div className="mt-4 space-y-3">
              {documents.map(doc => <div key={doc.id} className="flex items-center gap-3 rounded-2xl bg-slate-50 p-3">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-white text-violet-600"><FileText className="h-5 w-5" /></div>
                <div className="min-w-0 flex-1"><div className="truncate text-sm font-bold">{doc.filename}</div><div className="text-xs text-slate-400">{doc.chunk_count} 个知识片段 · {doc.status}</div></div>
                <button onClick={() => remove(doc.id)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-500"><X className="h-4 w-4" /></button>
              </div>)}
            </div>
          </Card>
        </div>
        <Card>
          <h3 className="font-black">检索实验室</h3>
          <p className="mt-1 text-xs text-slate-400">测试一个问题，观察 RAG 找到了哪些课程片段。</p>
          <div className="mt-4 flex gap-2"><input value={query} onChange={e => setQuery(e.target.value)} className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-violet-400" /><Button onClick={search}><Search className="h-4 w-4" />检索</Button></div>
          <div className="mt-5 space-y-3">
            {results.length ? results.map((item, i) => <div key={item.chunk_id} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between"><div className="text-xs font-bold text-violet-600">片段 {i + 1} · {item.title}</div><span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-bold text-emerald-700">相关度 {Math.round(item.score * 100)}%</span></div>
              <p className="mt-2 line-clamp-5 text-sm leading-6 text-slate-600">{item.content}</p>
            </div>) : <EmptyState title="尚未执行检索" text="输入课程问题，查看最相关的知识片段。" />}
          </div>
        </Card>
      </div>
    </>
  )
}
