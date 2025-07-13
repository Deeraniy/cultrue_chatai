<template>
  <div
    class="pixel-recommend-card"
    style="width: 800px; height: 700px; position: relative; margin: 40px auto;"
  >
    <img :src="homeBg" alt="白板背景" style="position:absolute; left:0; top:-20px; width:800px; height:700px; z-index:0; pointer-events:none;" />
    <div class="whiteboard-content">
      <h2 class="pixel-title">文学智能推荐（RAG）</h2>
      <div class="input-row">
        <input v-model="userInput" @keyup.enter="getRecommend" placeholder="说说你的心情或需求..." class="pixel-input" />
        <button @click="getRecommend" class="pixel-btn">推荐</button>
      </div>
      <div v-if="loading" style="margin: 20px 0; text-align: center; color: #888;">正在为你生成推荐...</div>
      <div v-if="error" style="color: red; margin-bottom: 16px;">{{ error }}</div>
    </div>
  </div>
  <div v-if="recommendList.length && !loading" class="recommend-result">
    <div style="margin-bottom: 24px;">
      <h3 class="pixel-title" style="margin-bottom: 8px;">最推荐：{{ recommendList[selectedIdx].liter_name }}</h3>
      <div style="margin-bottom: 8px; color: #333;">推荐理由：{{ recommendList[selectedIdx].reason }}</div>
      <button @click="addToPlan(recommendList[selectedIdx])" :style="`margin-top: 8px; padding: 6px 18px; border-radius: 6px; background: url('${brownPng}') no-repeat center center; background-size: cover; color: #fff; border: none; font-weight: bold;`">加入阅读计划</button>
    </div>
    <div v-if="recommendList.length > 1" style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
      <span style="color: #333; margin-right: 8px;">切换推荐：</span>
      <button v-for="(item, idx) in recommendList" :key="item.liter_id" @click="selectedIdx = idx" :style="buttonStyle(idx)">
        {{ item.liter_name }}
      </button>
    </div>
  </div>
  <div v-if="planLoading" style="margin-top: 16px; color: #409eff; text-align: center;">
    <span class="spinner" style="display:inline-block;width:24px;height:24px;border:3px solid #409eff;border-top:3px solid #fff;border-radius:50%;animation:spin 1s linear infinite;vertical-align:middle;"></span>
    <span style="margin-left:8px;">计划生成中...</span>
  </div>

  <!-- 在推荐卡片下方插入像素风计划卡片展示 -->
  <div v-if="planObj" class="reading-plan-card">
    <div class="plan-title">已加入阅读计划！</div>
    <div class="plan-meta"><b>书名：</b>{{ planObj.book }}</div>
    <div class="plan-meta"><b>总天数：</b>{{ planObj.total_days }}</div>
    <div class="plan-meta"><b>每日任务：</b></div>
    <ul>
      <li v-for="item in planObj.daily_plan" :key="item.day">
        第{{ item.day }}天：{{ item.task }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import brownPng from '@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown.png'
import homeBg from '@/assets/home_bg.png'

const userInput = ref('')
const recommendList = ref([])
const selectedIdx = ref(0)
const loading = ref(false)
const error = ref('')
const planMsg = ref('')
const planObj = ref(null)
const planLoading = ref(false)

async function getRecommend() {
  if (!userInput.value) return;
  loading.value = true;
  error.value = '';
  recommendList.value = [];
  selectedIdx.value = 0;
  planMsg.value = '';
  try {
    const res = await fetch('http://localhost:8000/api/chatbot/recommend/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `text=${encodeURIComponent(userInput.value)}`
    });
    const data = await res.json();
    if (data.recommend && data.recommend.length) {
      recommendList.value = data.recommend;
      selectedIdx.value = 0;
    } else {
      error.value = '未能获得推荐结果';
    }
  } catch (e) {
    error.value = '请求失败，请检查后端服务';
  } finally {
    loading.value = false;
  }
}

function buttonStyle(idx) {
  return {
    padding: '6px 16px',
    borderRadius: '6px',
    border: idx === selectedIdx.value ? '2px solid #409eff' : '1px solid #ccc',
    background: idx === selectedIdx.value ? '#e6f0ff' : '#f9f9f9',
    color: idx === selectedIdx.value ? '#409eff' : '#333',
    cursor: 'pointer',
    fontWeight: idx === selectedIdx.value ? 'bold' : 'normal'
  }
}

async function addToPlan(book) {
  planMsg.value = '';
  planObj.value = null;
  planLoading.value = true;
  try {
    const res = await fetch('http://localhost:8000/api/chatbot/join_plan/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: "test_user", // 实际项目应从登录信息获取
        book_name: book.liter_name
      })
    });
    const data = await res.json();
    if (data.plan) {
      planMsg.value = data.message ? data.message : '已加入阅读计划！';
      // 尝试解析JSON
      let planText = data.plan.trim();
      // 去除markdown代码块包裹
      if (planText.startsWith('```json')) planText = planText.replace(/^```json/, '').replace(/```$/, '').trim();
      try {
        planObj.value = JSON.parse(planText);
      } catch (e) {
        planObj.value = null;
        planMsg.value += '\n(计划内容解析失败，原文如下)';
        planMsg.value += '\n' + planText;
      }
    } else {
      planMsg.value = data.error || data.message || '加入失败';
    }
  } catch (e) {
    planMsg.value = '请求失败，未能加入计划';
  } finally {
    planLoading.value = false;
  }
}
</script>

<style scoped>
body {
  background: #f5f6fa;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.pixel-title {
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  color: #6b4f3b;
  text-shadow: 1px 1px 0 #fff, 2px 2px 0 #d9bfa3;
  letter-spacing: 1px;
}
.pixel-card {
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  
  border: 1px solid #ccc;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 1px 1px 0 #fff, 2px 2px 0 #d9bfa3;
}

.pixel-recommend-card {
  position: relative;
  /* width/height/background 由内联style控制 */
  margin: 40px auto;

  overflow: hidden;
  border: 4px solid transparent;

}

/* 精确定位到白板区域，并整体下移 */
.whiteboard-content {
  position: absolute;
  left: 200px;
  top: 180px;

  width: 400px;
  height: 640px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}

.recommend-result {
  width: 800px;
  margin: -102px auto 0 auto;
  background: #fffbe6;
  color: #333;
  border-radius: 18px;
  border: 4px solid #b48a78;
  box-shadow: 0 4px 16px rgba(180,138,120,0.13), 0 1.5px 0 #e6cfa7 inset;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  font-size: 17px;
  line-height: 1.8;
  letter-spacing: 0.5px;
  padding: 32px 36px 24px 36px;
  box-sizing: border-box;
}
.input-row {
  display: flex;
  gap: 12px;
  margin-top: 18px;
  width: 100%;
  justify-content: center;
}
.pixel-input {
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  border: 4px solid transparent;
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/white_inlay.png') 8 fill stretch;
  background: none;
  color: #6b4f3b;
  padding: 8px 12px;
  font-size: 16px;
  width: 180px;
  margin-right: 8px;
}
.pixel-btn {
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  border: 4px solid transparent;
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown.png') 8 fill stretch;
  background: none;
  color: #fff;
  padding: 8px 20px;
  font-size: 16px;
  cursor: pointer;
  transition: border-image 0.1s;
}
.pixel-btn:active {
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown_pressed.png') 8 fill stretch;
}

.reading-plan-card {
  background: #fffbe6;
  border: 4px solid #b48a78;
  border-radius: 14px;
  box-shadow: 0 4px 16px rgba(180,138,120,0.13), 0 1.5px 0 #e6cfa7 inset;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  color: #6b4f3b;
  padding: 32px 40px 28px 40px;
  margin: 32px auto;
  width: 90%;
  max-width: 900px;
  font-size: 17px;
  line-height: 2;
  letter-spacing: 0.5px;
  position: relative;
}

.reading-plan-card .plan-title {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 12px;
  color: #a05c2a;
  letter-spacing: 2px;
}

.reading-plan-card .plan-meta {
  font-size: 16px;
  margin-bottom: 10px;
  color: #8a6d3b;
}

.reading-plan-card ul {
  margin: 0 0 0 24px;
  padding: 0;
  list-style: none;
}

.reading-plan-card li {
  margin-bottom: 8px;
  position: relative;
  padding-left: 0;
}

.reading-plan-card li::before {
  content: '◆';
  color: #c97c4b;
  margin-right: 8px;
  font-size: 15px;
  vertical-align: middle;
}
</style>
