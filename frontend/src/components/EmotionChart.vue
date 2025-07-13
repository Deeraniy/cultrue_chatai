<!-- eslint-disable -->
<template>
  <div style="max-width: 700px; margin: 40px auto; padding: 24px; border-radius: 12px; background: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown.png') repeat; box-shadow: 0 2px 12px #eee;">
    <h2 class="pixel-title" style="margin-bottom: 26px;">情绪曲线图</h2>
    <div v-if="!userId || !book" style="margin-bottom: 16px; display: flex; gap: 8px; align-items: center;">
      <input v-model="userIdInput" placeholder="输入用户ID" style="padding: 8px; border-radius: 6px; border: none; width: 200px; background: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown.png') repeat; color: #6b4f3b;" />
      <input v-model="bookInput" placeholder="输入书名（可选）" style="padding: 8px; border-radius: 6px; border: none; width: 200px; background: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown.png') repeat; color: #6b4f3b; margin-left: 8px;" />
      <button @click="fetchData" style="margin-left: 8px; padding: 8px 20px; border-radius: 6px; background: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown.png') repeat; color: #fff; border: none; font-weight: bold;">查询</button>
    </div>
    <div v-if="loading" style="color: #fff; text-align: center; margin: 20px 0;">加载中...</div>
    <div v-if="error" style="color: #fff; margin-bottom: 16px;">{{ error }}</div>
    <div ref="chartRef" style="width: 100%; height: 400px;"></div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'EmotionChart',
  props: {
    userId: { type: String, default: '' },
    book: { type: String, default: '' }
  },
  setup(props) {
    const userIdInput = ref(props.userId || 'test_user')
    const bookInput = ref(props.book || '')
    const chartRef = ref(null)
    const chart = ref(null)
    const loading = ref(false)
    const error = ref('')
    const data = ref([])

    const effectiveUserId = computed(() => props.userId || userIdInput.value)
    const effectiveBook = computed(() => props.book || bookInput.value)

    function renderChart() {
      if (!chartRef.value) return
      if (!chart.value) {
        chart.value = echarts.init(chartRef.value)
      }
      if (!data.value.length) {
        chart.value.clear()
        return
      }
      const dates = data.value.map(d => d.date)
      const actual = data.value.map(d => d.predicted ? null : d.emotion)
      const predicted = data.value.map(d => d.predicted ? d.emotion : null)
      chart.value.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['实际值', '预测值'] },
        xAxis: { type: 'category', data: dates },
        yAxis: { type: 'value', min: 0, max: 1 },
        series: [
          {
            name: '实际值',
            type: 'line',
            data: actual,
            showSymbol: true,
            itemStyle: { color: '#409eff' },
            lineStyle: { width: 3 },
            connectNulls: false,
          },
          {
            name: '预测值',
            type: 'line',
            data: predicted,
            showSymbol: true,
            itemStyle: { color: '#faad14' },
            lineStyle: { type: 'dashed', width: 2 },
            connectNulls: false,
          }
        ]
      })
    }

    async function fetchData() {
      if (!effectiveUserId.value) {
        error.value = '请输入用户ID';
        return;
      }
      loading.value = true;
      error.value = '';
      try {
        let url = `/api/chatbot/emotion_curve/?user_id=${encodeURIComponent(effectiveUserId.value)}`
        if (effectiveBook.value) {
          url += `&book=${encodeURIComponent(effectiveBook.value)}`
        }
        const res = await fetch(url)
        const arr = await res.json()
        data.value = arr
        renderChart()
      } catch (e) {
        error.value = '请求失败';
      } finally {
        loading.value = false;
      }
    }

    onMounted(() => {
      fetchData()
    })

    watch([data, effectiveUserId, effectiveBook], () => {
      renderChart()
    })
    watch([effectiveUserId, effectiveBook], () => {
      fetchData()
    })

    return {
      userIdInput,
      bookInput,
      chartRef,
      loading,
      error,
      data,
      fetchData
    }
  }
}
</script>

<style scoped>
.pixel-title {
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  color: #6b4f3b;
  text-shadow: 1px 1px 0 #fff, 2px 2px 0 #d9bfa3;
  letter-spacing: 1px;
}
</style> 