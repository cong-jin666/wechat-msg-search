/**
 * 高亮渲染：把服务端 FTS5 snippet 里的哨兵字符「« »」变成 <mark>。
 *
 * 顺序不能反：
 *   1) 先 escapeHtml —— 用户消息内容完全不可信，任何 < > & " ' 都要转义；
 *   2) 再把哨兵「«»」替换成标签。
 * 哨兵是服务端插入的、不可能出现在原始文本里的字符，所以「转义后再还原」
 * 能保证标签只来自我们，绝不会来自用户内容。反过来先替换再转义，
 * 自己生成的 <mark> 也会被转掉。
 */

const ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

export function escapeHtml(text) {
  return String(text ?? '').replace(/[&<>"']/g, (c) => ESCAPE_MAP[c]);
}

export function renderHighlight(hit) {
  const source = hit?.snippet || hit?.content || '';
  return escapeHtml(source).replace(/«/g, '<mark>').replace(/»/g, '</mark>');
}
