import { ref, onUnmounted } from 'vue';

/**
 * SSE 流式接收（EventSource）。
 *
 * 注意 EventSource 的局限，也是为什么分析接口这里可以用它：
 *   - 只能 GET、不能带自定义请求头（没法放 Authorization）；
 *   - 只能收 text/event-stream 文本；
 *   - 断线重连是浏览器内置的，不用自己写心跳。
 * 如果将来接口要 POST + 鉴权头，就得换成 fetch + ReadableStream 手动解析流。
 */
export function useSSE() {
  const text = ref('');
  const status = ref('');
  const error = ref('');
  const streaming = ref(false);

  let source = null;

  function close() {
    if (source) {
      source.close();
      source = null;
    }
  }

  function run(url) {
    close();
    text.value = '';
    error.value = '';
    status.value = '已连接';
    streaming.value = true;

    source = new EventSource(url);

    source.addEventListener('chunk', (event) => {
      try {
        text.value += JSON.parse(event.data).text ?? '';
      } catch {
        text.value += event.data;
      }
    });

    source.addEventListener('done', () => {
      status.value = '完成';
      streaming.value = false;
      close();
    });

    // 服务端主动发 event: error 时 data 有内容；连接层错误时没有 data
    source.addEventListener('error', (event) => {
      if (event.data) {
        try {
          error.value = JSON.parse(event.data).message || '服务端错误';
        } catch {
          error.value = '服务端错误';
        }
      } else if (source && source.readyState === EventSource.CLOSED) {
        error.value = '连接中断';
      } else {
        return; // CONNECTING：浏览器正在自动重连，先不算失败
      }
      status.value = '失败';
      streaming.value = false;
      close();
    });
  }

  onUnmounted(close);

  return { text, status, error, streaming, run, close };
}
