import type { ReactNode } from 'react'

// A light Markdown renderer for the decision records: headings, paragraphs, nested bullet lists, fenced
// code, and inline code, bold, italic and links. It builds React elements, never HTML strings, so nothing
// in a record can inject markup.

const INLINE = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*\s][^*]*\*)|(\[[^\]]+\]\([^)\s]+\))/g

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = []
  let last = 0
  for (const m of text.matchAll(INLINE)) {
    const [token] = m
    if (m.index > last) out.push(text.slice(last, m.index))
    const key = out.length
    if (token.startsWith('`')) out.push(<code key={key}>{token.slice(1, -1)}</code>)
    else if (token.startsWith('**')) out.push(<strong key={key}>{inline(token.slice(2, -2))}</strong>)
    else if (token.startsWith('*')) out.push(<em key={key}>{inline(token.slice(1, -1))}</em>)
    else {
      const [, label, href] = token.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/)!
      out.push(/^https?:\/\//.test(href) ? <a key={key} href={href}>{inline(label)}</a> : inline(label))
    }
    last = m.index + token.length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

type Item = { text: string; children: Item[] }

// Bullet lines into a tree, by indent.
function listTree(lines: string[]): Item[] {
  const root: Item[] = []
  const stack: { indent: number; items: Item[] }[] = [{ indent: -1, items: root }]
  for (const line of lines) {
    const m = line.match(/^(\s*)- (.*)$/)
    if (!m) {
      // A wrapped continuation line joins the last item.
      const items = stack[stack.length - 1].items
      if (items.length) items[items.length - 1].text += ` ${line.trim()}`
      continue
    }
    const indent = m[1].length
    while (stack.length > 1 && indent <= stack[stack.length - 1].indent) stack.pop()
    const parent = stack[stack.length - 1].items
    const item = { text: m[2], children: [] }
    parent.push(item)
    stack.push({ indent, items: item.children })
  }
  return root
}

function list(items: Item[], key: number): ReactNode {
  return (
    <ul key={key}>
      {items.map((item, i) => (
        <li key={i}>
          {inline(item.text)}
          {item.children.length > 0 && list(item.children, 0)}
        </li>
      ))}
    </ul>
  )
}

// Renders Markdown blocks; headings are shifted down by `shift` levels so a record's title fits the page.
export function Markdown({ source, shift = 0 }: { source: string; shift?: number }) {
  const lines = source.replace(/\r\n/g, '\n').split('\n')
  const blocks: ReactNode[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    if (!line.trim()) {
      i++
    } else if (line.startsWith('```')) {
      const body: string[] = []
      for (i++; i < lines.length && !lines[i].startsWith('```'); i++) body.push(lines[i])
      i++
      blocks.push(<pre key={blocks.length}><code>{body.join('\n')}</code></pre>)
    } else if (/^#{1,6} /.test(line)) {
      const [, hashes, text] = line.match(/^(#{1,6}) (.*)$/)!
      const Tag = `h${Math.min(6, hashes.length + shift)}` as 'h2'
      blocks.push(<Tag key={blocks.length}>{inline(text)}</Tag>)
      i++
    } else if (/^\s*- /.test(line)) {
      const body: string[] = []
      for (; i < lines.length && lines[i].trim() && !/^#{1,6} /.test(lines[i]); i++) body.push(lines[i])
      blocks.push(list(listTree(body), blocks.length))
    } else {
      const body: string[] = []
      for (; i < lines.length && lines[i].trim() && !/^(#{1,6} |```|\s*- )/.test(lines[i]); i++) body.push(lines[i].trim())
      blocks.push(<p key={blocks.length}>{inline(body.join(' '))}</p>)
    }
  }
  return <>{blocks}</>
}
