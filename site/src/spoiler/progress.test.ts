import { describe, expect, it } from 'vitest'
import { badgeLabel, episodeLabel, progressLabel, reachedEpisode, spoilersHidden, type Episode } from './progress'

const episodes: Episode[] = [
  { episode: '1-01', part: 1, opening: 'When they came', words: 1, pages: null, summary: '' },
  { episode: '1-02', part: 1, opening: 'They rode', words: 1, pages: null, summary: '' },
  { episode: '2-01', part: 2, opening: 'He was all day', words: 1, pages: null, summary: '' },
]

describe('reachedEpisode', () => {
  it('sorts before and after every episode for none and all', () => {
    expect(reachedEpisode('none') < '1-01').toBe(true)
    expect(reachedEpisode('all') > '4-14').toBe(true)
    expect(reachedEpisode('2-05')).toBe('2-05')
  })
})

describe('spoilersHidden', () => {
  it('is on until the last episode is read', () => {
    expect(spoilersHidden('none', episodes)).toBe(true)
    expect(spoilersHidden('1-02', episodes)).toBe(true)
    expect(spoilersHidden('2-01', episodes)).toBe(false)
    expect(spoilersHidden('all', episodes)).toBe(false)
  })
  it('stays on while the episode list is loading', () => {
    expect(spoilersHidden('2-01', [])).toBe(true)
  })
})

describe('labels', () => {
  it('names a setting by Part, episode and opening words', () => {
    expect(progressLabel('2-01', episodes)).toBe('Part II, episode 1: He was all day')
    expect(progressLabel('none', episodes)).toBe('Not started')
    expect(progressLabel('3-01', episodes)).toBe('Episode 3-01')
    expect(episodeLabel('1-07')).toBe('Part I, episode 7')
  })
  it('says on the badge what the map hides', () => {
    expect(badgeLabel('none', false, episodes)).toBe('Not set')
    expect(badgeLabel('none', true, episodes)).toBe('Hiding the whole book')
    expect(badgeLabel('1-02', true, episodes)).toBe('Hiding what’s after Part I, episode 2: They rode')
    expect(badgeLabel('2-01', true, episodes)).toBe('Showing everything')
    expect(badgeLabel('all', true, episodes)).toBe('Showing everything')
  })
})
