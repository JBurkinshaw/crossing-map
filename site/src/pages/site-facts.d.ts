// Written at build time by scripts/site-facts.ts.
declare module 'virtual:site-facts' {
  type Counts = Record<string, number>
  type Column = {
    name: string
    type: string | string[] | null
    values: unknown[] | null
    description: string | null
    required: boolean
  }
  const facts: {
    layers: {
      name: string
      features: number
      geometry: string[]
      geojsonBytes: number | null
      parquetBytes: number | null
      certainty: Counts
      source: Counts
      method: Counts
      columns: Column[]
    }[]
    files: { file: string; bytes: number | null }[]
    dataBytes: number
    raisedBytes: number
    tileRelease: string
    tiles: { file: string; bytes: number }[]
  }
  export default facts
}
