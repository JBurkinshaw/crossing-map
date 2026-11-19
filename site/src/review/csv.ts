// A small CSV reader and writer for the review packets: quoted fields, doubled quotes, commas and newlines inside quotes.

export function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let quoted = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') {
        field += '"'
        i++
      } else if (c === '"') quoted = false
      else field += c
    } else if (c === '"') quoted = true
    else if (c === ',') {
      row.push(field)
      field = ''
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++
      row.push(field)
      rows.push(row)
      row = []
      field = ''
    } else field += c
  }
  if (field !== '' || row.length > 0) {
    row.push(field)
    rows.push(row)
  }
  const [head, ...body] = rows.filter((r) => r.some((f) => f !== ''))
  return head ? body.map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] ?? '']))) : []
}

export function toCsv(columns: string[], rows: Record<string, string>[]): string {
  const cell = (v: string) => (/[",\n\r]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v)
  return [columns.join(','), ...rows.map((r) => columns.map((c) => cell(r[c] ?? '')).join(','))].join('\n') + '\n'
}
