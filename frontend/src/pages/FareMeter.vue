<script setup>
import { ref } from 'vue'
import { postJSON, errorText } from '../api'
const distance_km = ref(8)
const slow_min = ref(3)
const dead_km = ref(0)
const night = ref(false)
const out = ref(null)
const err = ref('')
const run = async () => {
  err.value = ''
  try {
    out.value = await postJSON('/api/fare', {
      distance_km: distance_km.value, slow_min: slow_min.value,
      dead_km: Number(dead_km.value) || 0, night: night.value, persist: true,
    })
  } catch (e) { err.value = errorText(e) }
}
</script>
<template>
  <div class="page"><h1>打表试算</h1>
    <div class="panel">
      <label>载客公里 <input type="number" min="0" v-model.number="distance_km" /></label>
      <label>载客低速分钟 <input type="number" min="0" v-model.number="slow_min" /></label>
      <label>空驶公里 <input type="number" min="0" v-model.number="dead_km" /></label>
      <label><input type="checkbox" v-model="night" /> 夜间</label>
      <button @click="run">计算</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <div v-if="out" class="panel">
      <p class="hero-num">应付 ¥{{ out.payable }}</p>
      <p>载客应付 ¥{{ out.occupied_total }}
        （起步 {{ out.start }} · 里程 {{ out.mileage }} · 低速 {{ out.slow_fee }}<template v-if="out.night"> · 夜间×{{ out.night_factor }}</template>）</p>
      <p>空驶 {{ out.dead_km }} 公里 × {{ out.dead_price_per_km }} 元 = <strong>空驶费 ¥{{ out.dead_fee }}</strong></p>
    </div>
  </div>
</template>
