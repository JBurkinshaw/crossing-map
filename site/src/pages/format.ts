export const REPO_URL = 'https://github.com/JBurkinshaw/crossing-map'

// A new GitHub issue with its title and body filled in: how readers send corrections.
export function issueUrl(title: string, body: string): string {
  return `${REPO_URL}/issues/new?${new URLSearchParams({ title, body })}`
}
// The published data, as copied into the site by scripts/copy-data.mjs.
export const DATA_URL = `${import.meta.env.BASE_URL}data/`

export function bytes(n: number | null): string {
  if (n === null) return 'missing'
  if (n < 1000) return `${n} B`
  if (n < 1e6) return `${Math.round(n / 1000)} KB`
  return `${(n / 1e6).toFixed(1)} MB`
}

// The file name a layer is published under, and a readable label for it.
export function layerLabel(name: string): string {
  return name.replace('_', ' ').replace(/^./, (c) => c.toUpperCase())
}
