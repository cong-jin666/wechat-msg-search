<script setup>
import { ref } from 'vue';
import SearchView from './components/SearchView.vue';
import IngestView from './components/IngestView.vue';
import AnalyzeView from './components/AnalyzeView.vue';

const VALID_TABS = ['search', 'ingest', 'analyze'];
const initial = new URLSearchParams(location.search).get('tab');
const tab = ref(VALID_TABS.includes(initial) ? initial : 'search');

const tabs = [
  { key: 'search', label: '检索' },
  { key: 'ingest', label: '解析建库' },
  { key: 'analyze', label: '分析' },
];
</script>

<template>
  <div class="wrap">
    <header>
      <h1>微信聊天记录智能检索</h1>
      <p>数据仅在本机处理，不上传、不持久化到服务端存储以外的位置。</p>
    </header>

    <nav class="tabs">
      <button
        v-for="item in tabs"
        :key="item.key"
        :class="{ active: tab === item.key }"
        @click="tab = item.key"
      >
        {{ item.label }}
      </button>
    </nav>

    <SearchView v-show="tab === 'search'" />
    <IngestView v-show="tab === 'ingest'" />
    <AnalyzeView v-show="tab === 'analyze'" />
  </div>
</template>
