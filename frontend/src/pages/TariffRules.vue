<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON, putJSON } from '../api'
const t = ref(null)
const rates = ref([])
const newPrice = ref(1.5)
const err = ref('')
const load = async () => {
  t.value = await getJSON('/api/tariff')
  rates.value = (await getJSON('/api/empty-rates')).items
}
const create = async () => {
  err.value = ''
  try {
    await postJSON('/api/empty-rates', { per_km: newPrice.value, active: rates.value.every(r => !r.active) })
    await load()
  } catch (e) { err.value = e.message }
}
const save = async (r) => {
  err.value = ''
  try {
    await putJSON(`/api/empty-rates/${r.id}`, { per_km: r.per_km })
    await load()
  } catch (e) { err.value = e.message }
}
const toggle = async (r) => {
  err.value = ''
  try {
    await postJSON(`/api/empty-rates/${r.id}/active`, { active: !r.active })
    await load()
  } catch (e) { err.value = e.message }
}
onMounted(load)
</script>
<template>
  <div class="page"><h1>运价表</h1>
    <div class="panel" v-if="t">
      <p>起步 ¥{{ t.start_price }}（含 {{ t.start_include_km }}km） · 里程 ¥{{ t.per_km }}/km · 低速 ¥{{ t.per_slow_min }}/分 · 夜间 ×{{ t.night_factor }}</p>
    </div>
    <h2>空驶单价</h2>
    <p v-if="err" class="err">{{ err }}</p>
    <table>
      <tr><th>#</th><th>单价/km</th><th>状态</th><th></th></tr>
      <tr v-for="r in rates" :key="r.id">
        <td>#{{ r.id }}</td>
        <td><input type="number" step="0.1" v-model.number="r.per_km" /></td>
        <td>{{ r.active ? '启用中' : '已停用' }}</td>
        <td>
          <button @click="save(r)">保存</button>
          <button @click="toggle(r)">{{ r.active ? '停用' : '启用' }}</button>
        </td>
      </tr>
    </table>
    <div class="panel">
      <label>新单价 <input type="number" step="0.1" v-model.number="newPrice" /></label>
      <button @click="create">新增</button>
    </div>
  </div>
</template>
