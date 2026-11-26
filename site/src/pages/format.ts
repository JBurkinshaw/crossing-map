import facts from 'virtual:site-facts'

export const REPO_URL = 'https://github.com/JBurkinshaw/crossing-map'

// A file or folder in the repository at the commit this site was built from, so the link matches the code.
export const repoUrl = (path: string) => `${REPO_URL}/tree/${facts.commit}/${path}`

// The Tally form readers send corrections and better translations through (decision 0044): the id in its share
// link, tally.so/r/<id>. While it is empty, every link to the form hides.
export const FEEDBACK_FORM = '8Nxqrx'

// What a link fills into the form's hidden fields, so a suggestion arrives naming what it is about.
type Feedback =
  | { kind: 'correction'; feature: string; name: string }
  | { kind: 'translation'; line: string; episode: string }
  | { kind: 'general' }

// The form, with its hidden fields filled in, or null while there is no form.
export function feedbackUrl(fields: Feedback): string | null {
  if (!FEEDBACK_FORM) return null
  return `https://tally.so/r/${FEEDBACK_FORM}?${new URLSearchParams(fields)}`
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
