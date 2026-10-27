/**
 * 统一的接口客户端：错误归一化 + 可取消。
 *
 * 所有请求都接受一个 AbortSignal —— 视图层用它取消在途请求，
 * 避免「先发的请求后返回」把新结果覆盖掉（竞态）。
 */

async function parseError(res) {
  try {
    const body = await res.json();
    return body.detail || res.statusText;
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

async function request(url, { method = 'GET', params, body, signal } = {}) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  const res = await fetch(url + qs, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export const api = {
  get: (url, params, signal) => request(url, { params, signal }),
  post: (url, body, signal) => request(url, { method: 'POST', body, signal }),
};
