<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const distance_km = ref(8)
const slow_min = ref(3)
const empty_km = ref(0)
const night = ref(false)
const out = ref(null)
const err = ref('')
const run = async () => {
  err.value = ''
  try {
    out.value = await postJSON('/api/fare', { distance_km: distance_km.value, slow_min: slow_min.value, night: night.value, empty_km: empty_km.value, persist: true })
  } catch (e) { err.value = e.message; out.value = null }
}
</script>
<template>
  <div class="page"><h1>打表试算</h1>
    <div class="panel">
      <label>载客公里 <input type="number" v-model.number="distance_km" /></label>
      <label>低速分钟 <input type="number" v-model.number="slow_min" /></label>
      <label>空驶公里 <input type="number" v-model.number="empty_km" /></label>
      <label><input type="checkbox" v-model="night" /> 夜间</label>
      <button @click="run">计算</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <template v-if="out">
      <p class="hero-num">¥{{ out.payable }}</p>
      <p>起步 {{ out.start }} · 里程 {{ out.mileage }} · 低速 {{ out.slow_fee }} · 空驶 {{ out.empty_fee }}</p>
    </template>
  </div>
</template>
