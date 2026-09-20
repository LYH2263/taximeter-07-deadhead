export async function getJSON(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
export async function sendJSON(path, method, body) {
  const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
export const postJSON = (path, body) => sendJSON(path, 'POST', body)
export const patchJSON = (path, body) => sendJSON(path, 'PATCH', body)

export function errorText(e) {
  try {
    const d = JSON.parse(e.message)
    if (typeof d.detail === 'string') return d.detail
    if (Array.isArray(d.detail)) return d.detail.map(x => x.msg).join('；')
    if (d.detail) return JSON.stringify(d.detail)
  } catch { /* 原文已是可读消息 */ }
  return e.message
}
