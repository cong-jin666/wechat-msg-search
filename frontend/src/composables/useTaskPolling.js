import { ref, onUnmounted } from 'vue';
import { api } from '../api/client';

/**
 * 长任务状态轮询。
 *
 * 相比固定间隔轮询，这里做了两件事：
 *   1) 指数退避：800ms 起步，每次 ×1.5，上限 4s —— 任务跑两分钟也只会发几十个请求，
 *      而不是 150 个固定间隔请求；
 *   2) 失败容忍：单次网络抖动不再直接终止跟踪，连续失败 maxFailures 次才放弃。
 * 用 setTimeout 递归而不是 setInterval：保证上一次请求回来后才排下一次，
 * 不会出现请求堆积。
 */
export function useTaskPolling({ interval = 800, factor = 1.5, maxInterval = 4000, maxFailures = 3 } = {}) {
  const task = ref(null);
  const running = ref(false);
  const error = ref('');
  const result = ref(null);

  let timer = null;
  let failures = 0;
  let delay = interval;
  let onDone = null;

  function stop() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function schedule(fn, ms) {
    stop();
    timer = setTimeout(fn, ms);
  }

  async function tick(id) {
    try {
      const state = await api.get(`/api/tasks/${id}`);
      failures = 0;
      task.value = state;

      if (state.status === 'success') {
        running.value = false;
        result.value = state.result;
        stop();
        onDone?.(state);
        return;
      }
      if (state.status === 'failed') {
        running.value = false;
        error.value = state.error || '任务失败';
        stop();
        return;
      }
      delay = Math.min(delay * factor, maxInterval);
      schedule(() => tick(id), delay);
    } catch (e) {
      failures += 1;
      if (failures >= maxFailures) {
        running.value = false;
        error.value = `状态查询连续失败 ${failures} 次，已停止跟踪：${e.message}`;
        stop();
        return;
      }
      delay = Math.min(delay * 2, maxInterval);
      schedule(() => tick(id), delay);
    }
  }

  async function start(body = { kind: 'pipeline' }, { onSuccess } = {}) {
    stop();
    error.value = '';
    result.value = null;
    task.value = null;
    running.value = true;
    failures = 0;
    delay = interval;
    onDone = onSuccess || null;

    try {
      const created = await api.post('/api/tasks', body);
      schedule(() => tick(created.task_id), interval);
    } catch (e) {
      error.value = e.message;
      running.value = false;
    }
  }

  onUnmounted(stop);

  return { task, running, error, result, start, stop };
}
