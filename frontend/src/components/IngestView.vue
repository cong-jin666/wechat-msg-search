<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../api/client';
import { useTaskPolling } from '../composables/useTaskPolling';

const stats = ref({});
const statsError = ref('');
const { task, running, error, result, start } = useTaskPolling();

async function loadStats() {
  try {
    stats.value = await api.get('/api/stats');
    statsError.value = '';
  } catch (e) {
    statsError.value = e.message;
  }
}

function begin() {
  start({ kind: 'pipeline' }, { onSuccess: loadStats });
}

const percent = () => task.value?.percent ?? 0;

onMounted(loadStats);
</script>

<template>
  <section>
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <div class="stats" style="flex: 1">
          <div class="stat"><span>文本消息</span><strong>{{ stats.messages ?? '-' }}</strong></div>
          <div class="stat"><span>待分词</span><strong>{{ stats.segmented_pending ?? '-' }}</strong></div>
          <div class="stat"><span>待抽关键词</span><strong>{{ stats.keywords_pending ?? '-' }}</strong></div>
          <div class="stat"><span>索引行数</span><strong>{{ stats.fts_rows ?? '-' }}</strong></div>
        </div>
      </div>

      <div class="row" style="margin-top: 14px">
        <button class="primary" :disabled="running" @click="begin">
          {{ running ? '处理中…' : '开始解析建库' }}
        </button>
        <button class="primary ghost" @click="loadStats">刷新状态</button>
        <span v-if="task" class="meta">
          {{ task.status }} · {{ percent() }}%
          <span v-if="task.done">（{{ task.done }}/{{ task.total }}）</span>
        </span>
      </div>

      <div v-if="running || percent() < 100" class="bar"><i :style="{ width: percent() + '%' }"></i></div>

      <div v-if="result" class="meta">
        分词 {{ result.segmented }} 条 · 关键词 {{ result.keywords }} 条 · 索引 {{ result.indexed }} 行 ·
        耗时 {{ result.elapsed_ms }} ms
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="statsError" class="error">{{ statsError }}</div>
    </div>

    <div class="card">
      <div class="meta" style="margin-top: 0">
        解析是长任务：提交后返回 task_id，前端按指数退避轮询状态（800ms 起，上限 4s），
        避免一个 HTTP 请求跑几分钟被超时掐断。
      </div>
    </div>
  </section>
</template>
