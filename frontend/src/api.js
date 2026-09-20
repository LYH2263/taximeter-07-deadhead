async function req(path, opts) {
  const r = await fetch(path, opts)
  if (!r.ok) {
    const text = await r.text()
    let msg = text
    try {
      const d = JSON.parse(text).detail
      if (typeof d === 'string') msg = d
    } catch { /* 非 JSON 错误体，原文展示 */ }
    throw new Error(msg)
  }
  return r.json()
}
export function getJSON(path) { return req(path) }
export function postJSON(path, body) {
  return req(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
}
export function putJSON(path, body) {
  return req(path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
}
