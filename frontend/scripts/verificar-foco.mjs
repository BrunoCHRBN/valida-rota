// Verificação de foco por teclado, feita no navegador e não por leitura do CSS.
//
// Mede o que a leitura não mostra: em cada parada de Tab, o elemento ativo tem
// anel visível? E, no campo de hora, o anel sobrevive aos subcampos internos?
//
// Requer Playwright disponível para o Node (npm i -D playwright) e o frontend no ar.
//   node scripts/verificar-foco.mjs [url]
// Sai com código 1 se alguma parada de foco ficar sem anel.

import { chromium } from 'playwright'

const url = process.argv[2] ?? 'http://127.0.0.1:5173/'
const PARADAS = 46

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })
await page.goto(url, { waitUntil: 'networkidle' })

// gera resultado, para a varredura cobrir também a área de saída
const enviar = page.locator('form button[type=submit]')
if (await enviar.count()) {
  await enviar.click()
  await page.waitForTimeout(1500)
}

const estado = () =>
  page.evaluate(() => {
    const el = document.activeElement
    if (!el || el === document.body) return { corpo: true }
    const cs = getComputedStyle(el)
    const rotulo =
      (el.labels && el.labels[0] && el.labels[0].innerText) || el.getAttribute('aria-label') || el.innerText || el.value || ''
    return {
      tag: el.tagName,
      tipo: el.type ?? null,
      rotulo: String(rotulo).replace(/\s+/g, ' ').trim().slice(0, 34),
      anel: cs.outlineStyle === 'solid' && parseFloat(cs.outlineWidth) >= 2,
      rolagem: el.classList.contains('tabela-scroll'),
    }
  })

await page.evaluate(() => document.body.focus())

let total = 0
let alcancouRolagem = false
const semAnel = []
for (let i = 0; i < PARADAS; i++) {
  await page.keyboard.press('Tab')
  const e = await estado()
  if (e.corpo) continue
  total++
  if (e.rolagem) alcancouRolagem = true
  if (!e.anel) semAnel.push(`${i + 1}: ${e.tag}/${e.tipo} ${e.rotulo}`)
}

console.log(`paradas de foco: ${total}`)
console.log(`sem anel visível: ${semAnel.length}`)
semAnel.forEach((s) => console.log('  ', s))

// A tabela rola na horizontal em tela estreita; sem parada de foco no contêiner,
// o teclado não alcança as colunas da direita.
const temTabela = await page.locator('.tabela-scroll').count()
console.log(`contêiner da tabela alcançável por Tab: ${alcancouRolagem}`)
if (temTabela > 0 && !alcancouRolagem) semAnel.push('contêiner .tabela-scroll não recebe foco')

await browser.close()
process.exit(semAnel.length === 0 ? 0 : 1)
