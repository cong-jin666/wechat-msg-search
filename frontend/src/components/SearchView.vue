<script setup>
import { useSearch } from '../composables/useSearch';
import { renderHighlight } from '../utils/highlight';

const { query, expand, loading, hits, meta, error, run } = useSearch();
</script>

<template>
  <section>
    <div class="card">
      <div class="row">
        <input
          v-model="query"
          type="text"
          placeholder="输入关键词，例如：会议 / 天气 / 预算"
          @keyup.enter="run"
        />
        <label class="check"><input v-model="expand" type="checkbox" /> 近义词扩展</label>
        <button class="primary" :disabled="loading || !query.trim()" @click="run">
          {{ loading ? '检索中…' : '检索' }}
        </button>
      </div>

      <div v-if="meta" class="meta">
        模式 {{ meta.mode }} · 命中 {{ meta.count }} 条
        <span v-if="meta.terms.length > 1"> · 扩展词：{{ meta.terms.join(' / ') }}</span>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div class="card">
      <div v-if="!hits.length" class="empty">
        {{ meta ? '没有匹配的记录' : '输入关键词开始检索' }}
      </div>
      <div v-for="hit in hits" :key="hit.rowid" class="hit">
        <div>
          <span class="who">{{ hit.talker }}</span>
          <span class="time">{{ hit.created_at }}</span>
        </div>
        <!-- 正文经 escapeHtml 后再还原高亮标记，见 utils/highlight.js -->
        <div class="body" v-html="renderHighlight(hit)"></div>
      </div>
    </div>
  </section>
</template>
