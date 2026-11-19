import { Fragment } from 'react'
import type { Lead } from '../data/story'
import { SECOND_SOURCES } from '../data/sources'
import { distance, type Units } from '../units'

// The second sources that place a feature too (decision 0065): "Also placed by" for those that agree with the map's
// point, "Readers disagree" for those that put it elsewhere, with how far. One line each, in the faint meta style of
// the source line they sit beside. The leads have already passed the spoiler filter.
export function Leads({ leads, units }: { leads?: Lead[]; units: Units }) {
  const agree = leads?.filter((l) => l.relation === 'agrees') ?? []
  const differ = leads?.filter((l) => l.relation === 'differs') ?? []
  const entry = (l: Lead, i: number) => {
    const source = SECOND_SOURCES[l.source]
    return (
      <Fragment key={l.source}>
        {i > 0 && ' · '}
        {source ? <a href={source.link}>{source.credit}</a> : l.source}
        {l.page && `, p. ${l.page}`}
        {l.distance_km !== undefined && `, ${distance(l.distance_km * 1000, units)} away`}
        {l.note && ` (${l.note})`}
      </Fragment>
    )
  }
  return (
    <>
      {agree.length > 0 && (
        <p className="meta">
          <em>Also placed by</em> {agree.map(entry)}
        </p>
      )}
      {differ.length > 0 && (
        <p className="meta">
          <em>Readers disagree:</em> {differ.map(entry)}
        </p>
      )}
    </>
  )
}
