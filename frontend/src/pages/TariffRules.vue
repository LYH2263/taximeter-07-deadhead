<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, patchJSON, postJSON, errorText } from '../api'

const t = ref(null)
const rates = ref([])
const err = ref('')
const form = ref({ code: '', name: '', price_per_km: 1.5, active: false })

async function load() {
  t.value = await getJSON('/api/tariff')
  rates.value = (await getJSON('/api/dead-km-rates')).items
}
onMounted(load)

async function createRate() {
  err.value = ''
  try {
    await postJSON('/api/dead-km-rates', { ...form.value, price_per_km: Number(form.value.price_per_km) })
    form.value = { code: '', name: '', price_per_km: 1.5, active: false }
    await load()
  } catch (e) { err.value = errorText(e) }
}

async function savePrice(r) {
  err.value = ''
  try {
    await patchJSON(`/api/dead-km-rates/${r.id}`, { price_per_km: Number(r.price_per_km) })
    await load()
  } catch (e) { err.value = errorText(e); await load() }
}

async function toggle(r, active) {
  err.value = ''
  try {
    await patchJSON(`/api/dead-km-rates/${r.id}`, { active })
    await load()
  } catch (e) { err.value = errorText(e); await load() }
}
</script>
<template>
  <div class="page">
    <h1>运价表</h1>
    <div class="panel">
      <h2>载客运价</h2>
      <pre v-if="t">{{ t }}</pre>
    </div>

    <div class="panel">
      <h2>空驶单价</h2>
      <p class="muted">空驶段不加起步、不计低速；应付 = 载客应付 + 空驶单价 × 空驶公里。只允许一条启用，单价必须为正。</p>
      <p v-if="err" class="err">{{ err }}</p>
      <table>
        <tr><th>标识</th><th>名称</th><th>单价(元/公里)</th><th>状态</th><th>操作</th></tr>
        <tr v-for="r in rates" :key="r.id">
          <td>{{ r.code }}</td>
          <td>{{ r.name }}</td>
          <td><input type="number" min="0" step="0.1" v-model.number="r.price_per_km" />
            <button @click="savePrice(r)">改价</button></td>
          <td>{{ r.active ? '启用中' : '已停用' }}</td>
          <td>
            <button v-if="!r.active" @click="toggle(r, true)">启用</button>
            <button v-else @click="toggle(r, false)">停用</button>
          </td>
        </tr>
      </table>

      <h3>新增空驶单价</h3>
      <div class="panel">
        <label>标识 <input v-model="form.code" placeholder="如 standard" /></label>
        <label>名称 <input v-model="form.name" /></label>
        <label>单价 <input type="number" min="0" step="0.1" v-model.number="form.price_per_km" /></label>
        <label><input type="checkbox" v-model="form.active" /> 立即启用</label>
        <button @click="createRate">新增</button>
      </div>
    </div>
  </div>
</template>
