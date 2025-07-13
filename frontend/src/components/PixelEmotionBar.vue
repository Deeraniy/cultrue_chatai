<template>
  <div style="width: 100%;">
    <h2 class="pixel-title" style="margin-bottom: 10px; margin-top: 10px; display: block; margin-left: auto; margin-right: auto; text-align: center;">情绪进度条</h2>
    <div style="height: 40px;"></div>
    <div class="pixel-bar-chart-vertical-outer">
      <div v-if="mode === 'vertical'" class="pixel-bar-chart-vertical pixel-bar-chart-vertical-wide">
        <div v-for="(item, idx) in props.data" :key="idx" class="pixel-bar-cell-vertical">
          <div class="pixel-bar-label-vertical" style="margin-bottom: 12px;">{{ (item.date || '').slice(5) }}</div>
          <div class="pixel-bar-vertical">
            <div
              v-for="n in 20"
              :key="n"
              class="pixel-bar-vertical-cell"
              :class="{ predicted: item.predicted, filled: n <= Math.round(item.emotion * 20) }"
              :title="item.date + (item.predicted ? '（预测）' : '（实际）') + '：' + (item.emotion * 100).toFixed(0) + '%'"
            ></div>
          </div>
          <div class="pixel-bar-vertical-value">{{ Math.round(item.emotion * 100) }}%</div>
        </div>
      </div>
      <div v-else class="pixel-bar-chart-xp">
        <div v-for="(item, idx) in props.data" :key="idx" class="pixel-bar-xp-row">
          <div class="pixel-bar-label-xp">{{ item.date || (idx + 1) }}</div>
          <div class="pixel-bar-xp">
            <div
              v-for="n in 20"
              :key="n"
              class="pixel-bar-xp-cell"
              :class="{ predicted: item.predicted, filled: n <= Math.round(item.emotion * 20) }"
              :title="item.date + (item.predicted ? '（预测）' : '（实际）') + '：' + (item.emotion * 100).toFixed(0) + '%'"
            ></div>
          </div>
          <div class="pixel-bar-xp-value">{{ Math.round(item.emotion * 100) }}%</div>
        </div>
      </div>
    </div>
    <div class="pixel-emotion-bar-legend">
      <span v-if="mode === 'vertical'" class="pixel-bar-vertical-cell filled"></span>
      <span v-if="mode === 'vertical'" class="pixel-bar-vertical-cell filled predicted"></span>
      <span v-if="mode !== 'vertical'" class="pixel-bar-xp-cell filled"></span>
      <span v-if="mode !== 'vertical'" class="pixel-bar-xp-cell filled predicted"></span>
      实际值 <span style="margin-left: 10px;"></span> 预测值
    </div>
  </div>
</template>

<script setup>
// eslint-disable-next-line no-undef
const props = defineProps({
  data: { type: Array, default: () => [] },
  mode: { type: String, default: '' }
})
</script>

<style scoped>
.pixel-title {
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  color: #6b4f3b;
  text-shadow: 1px 1px 0 #fff, 2px 2px 0 #d9bfa3;
  letter-spacing: 1px;
  margin-top: 10px;
  margin-bottom:80px;
}
.pixel-bar-chart-vertical-outer {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 90px;
}
.pixel-bar-chart-vertical.pixel-bar-chart-vertical-wide {
  gap: 22px;
  min-width: 480px;
  max-width: 900px;
  justify-content: center;
}
.pixel-bar-chart-vertical {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  gap: 10px;
  height: 120px;
  min-height: 80px;
  margin-bottom: 8px;
  padding-bottom: 4px;
}
.pixel-bar-cell-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  width: 32px;
}
.pixel-bar-label-vertical {
  font-size: 9px;
  color: #b48a78;
  margin-bottom: 2px;
  text-align: center;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  word-break: break-all;
}
.pixel-bar-vertical {
  display: flex;
  flex-direction: column-reverse;
  gap: 2px;
}
.pixel-bar-vertical-cell {
  width: 26px;
  height: 6px;
  background: #e0e0e0;
  border: 1.5px solid #b48a78;
  box-sizing: border-box;
  margin: 0;
  border-radius: 0;
  display: block;
  transition: background 0.2s;
}
.pixel-bar-vertical-cell.filled {
  background: #409eff;
  border-color: #2766a7;
}
.pixel-bar-vertical-cell.filled.predicted {
  background: #faad14;
  border-color: #b48a78;
  opacity: 0.8;
}
.pixel-bar-vertical-value {
  font-size: 10px;
  color: #6b4f3b;
  margin-top: 2px;
  text-align: center;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
}
.pixel-emotion-bar-legend {
  margin-top: -5px;
  font-size: 13px;
  color: #6b4f3b;
  display: flex;
  gap: 18px;
  align-items: center;
  justify-content: center;
  width: 100%;
}
</style> 