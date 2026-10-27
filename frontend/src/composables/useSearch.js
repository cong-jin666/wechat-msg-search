import { ref, onMounted, onUnmounted } from 'vue';
import { api } from '../api/client';

/**
 * 检索逻辑。
 *
 * 竞态处理两层：
 *   1) AbortController —— 新请求发出前取消上一个在途请求；
 *   2) 请求序号 seq —— 万一旧响应已经进了回调队列，用序号把它丢弃。
 * 只做 1 也能挡住绝大多数情况，但两者叠加才是幂等的。
 */
export function useSearch() {
  const query = ref('');
  const expand = ref(true);
  const loading = ref(false);
  const hits = ref([]);
  const meta = ref(null);
  const error = ref('');

  let controller = null;
  let seq = 0;

  async function run() {
    const q = query.value.trim();
    if (!q) return;

    controller?.abort();
    controller = new AbortController();
    const mySeq = ++seq;

    loading.value = true;
    error.value = '';
    try {
      const data = await api.get(
        '/api/search',
        { q, limit: 50, expand: expand.value },
        controller.signal,
      );
      if (mySeq !== seq) return;
      hits.value = data.hits;
      meta.value = { mode: data.mode, count: data.count, terms: data.terms };
    } catch (e) {
      if (e.name === 'AbortError' || mySeq !== seq) return;
      error.value = e.message;
      hits.value = [];
      meta.value = null;
    } finally {
      if (mySeq === seq) loading.value = false;
    }
  }

  // URL 即状态：/?q=会议&expand=0 直接出结果，方便分享和自查
  onMounted(() => {
    const params = new URLSearchParams(location.search);
    const q = params.get('q');
    if (!q) return;
    query.value = q;
    if (params.get('expand') === '0') expand.value = false;
    run();
  });

  onUnmounted(() => controller?.abort());

  return { query, expand, loading, hits, meta, error, run };
}
