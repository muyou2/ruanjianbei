import { useEffect, useId, useState, type ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import { LoaderCircle, Sparkles } from 'lucide-react'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-3xl border border-white/80 bg-white/85 p-5 shadow-soft backdrop-blur ${className}`}>{children}</section>
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return (
    <header className="mb-7 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
      <div>
        <div className="mb-2 text-xs font-bold uppercase tracking-[.22em] text-violet-600">{eyebrow}</div>
        <h1 className="text-3xl font-black tracking-tight text-slate-900 lg:text-4xl">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{description}</p>
      </div>
      {action}
    </header>
  )
}

export function Button({ children, loading, className = '', ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean }) {
  return (
    <button
      {...props}
      disabled={props.disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-violet-200 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    >
      {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
      {children}
    </button>
  )
}

export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-slate max-w-none prose-headings:font-black prose-a:text-violet-600 prose-code:rounded prose-code:bg-violet-50 prose-code:px-1 prose-code:text-violet-700">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}

export function Mermaid({ chart }: { chart: string }) {
  const id = useId().replace(/:/g, '')
  const [svg, setSvg] = useState('')
  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: 'base', themeVariables: { primaryColor: '#ede9fe', primaryTextColor: '#312e81', lineColor: '#7c3aed' } })
    mermaid.render(`mermaid-${id}`, chart).then(({ svg }) => setSvg(svg)).catch(() => setSvg(''))
  }, [chart, id])
  return svg
    ? <div className="overflow-auto rounded-2xl bg-violet-50/70 p-5" dangerouslySetInnerHTML={{ __html: svg }} />
    : <pre className="overflow-auto rounded-2xl bg-slate-900 p-4 text-xs text-violet-100">{chart}</pre>
}

export function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="grid min-h-48 place-items-center rounded-3xl border border-dashed border-violet-200 bg-violet-50/50 p-8 text-center">
      <div><div className="text-3xl">✦</div><h3 className="mt-2 font-bold text-slate-800">{title}</h3><p className="mt-1 text-sm text-slate-500">{text}</p></div>
    </div>
  )
}
