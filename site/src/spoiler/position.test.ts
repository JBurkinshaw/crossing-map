import { describe, expect, it } from 'vitest'
import { episodeAtPage, episodeAtPercent, hasPages } from './position'
import type { Episode } from './progress'

const episode = (id: string, words: number, pages: string | null): Episode => ({
  episode: id,
  part: Number(id[0]),
  opening: id,
  words,
  pages,
  summary: '',
})
// 1,000 words in all: 10 %, 40 % and 50 % of the book.
const episodes = [episode('1-01', 100, null), episode('1-02', 400, null), episode('2-01', 500, null)]
const paged = [episode('1-01', 100, '5–24'), episode('1-02', 400, '24–60'), episode('2-01', 500, '61-120')]

describe('episodeAtPercent', () => {
  it('finds the episode holding that point of the book', () => {
    expect(episodeAtPercent(0, episodes)).toBe('none')
    expect(episodeAtPercent(5, episodes)).toBe('1-01')
    expect(episodeAtPercent(10, episodes)).toBe('1-01')
    expect(episodeAtPercent(10.1, episodes)).toBe('1-02')
    expect(episodeAtPercent(50, episodes)).toBe('1-02')
    expect(episodeAtPercent(100, episodes)).toBe('2-01')
  })
  it('refuses what is not a percentage', () => {
    expect(episodeAtPercent(-1, episodes)).toBeNull()
    expect(episodeAtPercent(101, episodes)).toBeNull()
    expect(episodeAtPercent(Number.NaN, episodes)).toBeNull()
    expect(episodeAtPercent(50, [])).toBeNull()
  })
})

describe('pages', () => {
  it('reads the first page of a range, with either dash', () => {
    // '5–24' has an en dash, '61-120' a hyphen.
    expect(episodeAtPage(5, paged)).toBe('1-01')
    expect(episodeAtPage(61, paged)).toBe('2-01')
  })
  it('works only once every episode has pages', () => {
    expect(hasPages(episodes)).toBe(false)
    expect(hasPages(paged)).toBe(true)
    expect(episodeAtPage(30, episodes)).toBeNull()
  })
  it('finds the episode a page falls in', () => {
    expect(episodeAtPage(3, paged)).toBe('none')
    expect(episodeAtPage(5, paged)).toBe('1-01')
    expect(episodeAtPage(24, paged)).toBe('1-02')
    expect(episodeAtPage(60, paged)).toBe('1-02')
    expect(episodeAtPage(400, paged)).toBe('2-01')
  })
})
