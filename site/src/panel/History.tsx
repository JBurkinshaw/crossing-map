import type { HistoryNote } from '../data/story'
import { SECOND_SOURCES } from '../data/sources'

// A feature's local history (decision 0071): a line for each note, cited by source and page, in the faint meta
// style of the second-source lines (decision 0065). The notes have already passed the spoiler filter.
export function History({ history }: { history?: HistoryNote[] }) {
  return (
    <>
      {history?.map((h, i) => {
        const source = SECOND_SOURCES[h.source]
        return (
          <p className="meta" key={i}>
            <em>Local history:</em> {h.note} ({source ? <a href={source.link}>{source.credit}</a> : h.source},{' '}
            {h.page.includes('–') ? 'pp.' : 'p.'} {h.page})
          </p>
        )
      })}
    </>
  )
}
