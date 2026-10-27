<script setup>
import { ref, watch, nextTick } from 'vue';
import { useSSE } from '../composables/useSSE';

const { text, status, error, streaming, run } = useSSE();
const box = ref(null);

function start() {
  run('/api/analyze?delay=0.05');
}

// 流式追加后 DOM 还没刷新，等本轮更新 flush 完再滚到底
watch(text, async () => {
  await nextTick();
  if (box.value) box.value.scrollTop = box.value.scrollHeight;
});
</script>

<template>
  <section>
    <div class="card">
      <div class="row">
        <button class="primary" :disabled="streaming" @click="start">
          {{ streaming ? '生成中…' : '生成分析摘要' }}
        </button>
        <span class="tag">SSE 流式</span>
        <span class="meta" style="margin: 0">{{ status }}</span>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div class="card">
      <pre ref="box" class="stream">{{ text || '点击上方按钮，服务端会以事件流的形式逐块返回结果。' }}</pre>
    </div>
  </section>
</template>
