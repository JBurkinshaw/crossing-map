// Open the Guild in the browsing profile so you can log in by hand.
// Usage: npm run guild-login. Log in, tick "Remember Me", then close the window.
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const PROFILE = path.join(fileURLToPath(new URL('../..', import.meta.url)), 'private', 'browser-profile')

const context = await chromium.launchPersistentContext(PROFILE, { channel: 'chrome-canary', headless: false, viewport: null })
const page = context.pages()[0] ?? (await context.newPage())
await page.goto('https://www.cartographersguild.com/forum.php')
console.log('Log in in the browser window, then close it.')
await new Promise((resolve) => context.on('close', resolve))
