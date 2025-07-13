<template>
  <div class="pixel-card pixel-tan-card">
    <!-- 顶部：切换书籍 -->
    <div style="margin: 0 0 16px 48px; display: flex; align-items: center; gap: 12px;">
      <label style="font-weight: bold;" class="pixel-title">切换书籍：</label>
      <select v-model="selectedBook" @change="onSelectBook" class="pixel-btn" style="padding: 4px 12px; min-width: 180px; background: #fff;">
        <option v-for="book in uniqueBooks" :key="book" :value="book">
          {{ book }}
        </option>
      </select>
    </div>
    <!-- 第一行：日历 + 情绪进度条 -->
    <div style="display: flex; gap: 24px; justify-content: center; align-items: flex-start; margin-bottom: 32px;">
      <!-- 日历（左侧） -->
      <div :style="{
        flex: 1,
        minWidth: '480px',
        maxWidth: '750px',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        background: `url(${calendarBg}) center -15px / 180% 115% no-repeat`,
        border: 'none',
        borderRadius: '0',
        boxShadow: 'none',
        padding: 0,
        margin: 0,
        minHeight: '445px'
      }">
        <h3 class="pixel-title" style="margin-bottom: 16px;margin-top: -5px;">阅读计划日历</h3>
        <div v-if="selectedPlanObj" style="margin-bottom: 8px; color: #6b4f3b;">总天数：{{ selectedPlanObj.total_days }}，规划范围：{{ selectedPlanObj.start_date }} ~ {{ selectedPlanObj.end_date }}</div>
        <!-- 日历表格和选中计划（保留原有逻辑） -->
        <div v-if="calendarRows && calendarRows.length" style="width: 100%; display: flex; justify-content: flex-start;">
          <div style="max-width: 360px; width: 100%; margin-left: 100px;margin-top:30px;">
            <div style="margin-top: 48px; margin-bottom: 8px; font-size: 16px; text-align: center; color: #6b4f3b;">
              {{ yyyy }}年{{ mm+1 }}月
            </div>
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <th v-for="d in ['日','一','二','三','四','五','六']" :key="d" style="padding: 4px; color: #6b4f3b;">{{ d }}</th>
              </tr>
              <tr v-for="(row, i) in calendarRows" :key="i">
                <td
                  v-for="cell in row"
                  :key="cell.date"
                  :style="calendarCellStyle(cell.date)"
                  @click="selectDate(cell.date, cell.day)"
                >
                  <div>{{ cell.day }}</div>
                  <div v-if="dailyStatus[cell.date]" style="font-size: 16px; color: #52c41a; margin-top: 2px;">√</div>
                  <div v-else-if="isPlanDay(cell.date)" style="font-size: 12px; color: #ccc; margin-top: 2px;">●</div>
                </td>
              </tr>
            </table>
          </div>
        </div>
      </div>
      <!-- 情绪进度条（右侧） -->
      <div :style="{
        flex: 1,
        minWidth: '600px',
        maxWidth: '1100px',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        background: `url(${motionBg}) center 180px / 80% 60% no-repeat`,
        border: 'none',
        borderRadius: '0',
        boxShadow: 'none',
        padding: 0,
        margin: 0,
        marginTop: '-60px',
        minHeight:'500px'
      }">
        <div v-if="selectedDay && selectedDayTask" style="margin-bottom: 20px; margin-top: 40px; padding: 16px; background: #fff; border-radius: 8px; border: 1px solid #ffe58f; color: #222; width: 100%; max-width: 420px;">
          <b>{{ selectedDay }} 的计划：</b>
          <div style="margin-top: 8px;">{{ selectedDayTask }}</div>
        </div>
        <div style="width: 100%; margin-top: -20px;">
          <PixelEmotionBar :data="emotionData" mode="vertical" />
        </div>
      </div>
    </div>
    <!-- 第二行：总计划 + 日记对话 -->
    <div style="display: flex; gap: 32px;">
      <!-- 总计划（左侧） -->
      <div class="pixel-inlay-card tan" style="flex: 1.2; min-width: 320px; max-width: 380px; display: flex; flex-direction: column; position: relative;">
        <div v-if="selectedPlanObj">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px; justify-content: flex-start;">
            <h3 class="pixel-title" style="margin: 0; color: #6b4f3b; margin-left: 32px;">当前计划</h3>
          </div>
          <div class="note-paper">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
              <div style="font-weight: bold; font-size: 18px;">书名：{{ selectedPlanObj.book }}</div>
              <button @click="editMode = true" class="pixel-btn pixel-blue" style="font-size: 15px; margin-left: 100px;">编辑计划</button>
            </div>
            <div style="font-weight: bold; margin-bottom: 8px;">总天数：{{ selectedPlanObj.total_days }}</div>
            <div style="font-weight: bold; margin-bottom: 8px;">每日任务：</div>
            <ul style="margin-left: 0; padding: 0;">
              <li v-for="item in selectedPlanObj.daily_plan" :key="item.day" style="display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 6px; padding: 0 2px;">
                <span style="font-weight: bold; min-width: 54px; color: #c97c4b;">第{{ item.day }}天：</span>
                <span style="flex: 1; text-align: left; color: #333;">{{ item.task }}</span>
              </li>
            </ul>
          </div>
          <div v-if="editMode">
            <div class="pixel-inlay-card" style="margin: 12px 0; padding: 18px; background: #fffbe6; border-radius: 12px; border: none; color: #222;">
              <div><b>书名：</b><input v-model="editPlanObj.book" class="pixel-btn" style="width: 60%; margin-left: 8px; background: #fff; color: #222;" /></div>
              <div><b>总天数：</b><input v-model.number="editPlanObj.total_days" type="number" min="1" class="pixel-btn" style="width: 60px; margin-left: 8px; background: #fff; color: #222;" /></div>
              <div><b>每日任务：</b></div>
              <ul style="margin-left: 16px;">
                <li v-for="(item, idx) in editPlanObj.daily_plan" :key="item.day">
                  <b>第{{ item.day }}天：</b><input v-model="editPlanObj.daily_plan[idx].task" class="pixel-btn" style="width: 70%; margin-left: 8px; background: #fff; color: #222;" />
                </li>
              </ul>
            </div>
            <button @click="saveEditPlan" class="pixel-btn" style="margin-top: 8px; padding: 8px 24px; background: url('@/assets/kenney_pixel-ui-pack/ancient/list.png') no-repeat center/cover; color: #222; border: none; font-size: 16px;">保存</button>
            <button @click="editMode = false" class="pixel-btn" style="margin-top: 8px; margin-left: 12px; padding: 8px 24px; background: url('@/assets/kenney_pixel-ui-pack/ancient/list.png') no-repeat center/cover; color: #222; border: none; font-size: 16px;">取消</button>
          </div>
        </div>
      </div>
      <!-- 日记+对话（右侧） -->
      <div style="flex: 1.2; display: flex; flex-direction: column; gap: 24px;">
        <div
          class="pixel-inlay-card"
          :style="{ background: `url(${diaryBg}) center center / 130% 110% no-repeat`, border: 'none' }"
          style="margin-bottom: 0;"
        >
          <h3 class="pixel-title" style="margin-bottom: 16px; color: #6b4f3b;">阅读日记</h3>
          <textarea
            v-model="diaryText"
            :readonly="!diaryEditMode"
            class="pixel-btn"
            placeholder="写下你的阅读感受..."
            style="width: 95%; min-height: 120px; max-height: 180px; overflow-y: auto; background: #fff; border-radius: 6px; border: 1px solid #ccc; padding: 8px; color: #222;"
          ></textarea>
          <div style="margin-top: 8px;">
            <button v-if="!diaryEditMode && selectedDay === dayjs().format('YYYY-MM-DD')" @click="onEditDiary" class="pixel-btn pixel-blue" style="padding: 6px 24px; border-radius: 8px; background: #409eff; color: #fff; border: none;">编辑</button>
            <button v-if="diaryEditMode && selectedDay === dayjs().format('YYYY-MM-DD')" @click="saveDiary" class="pixel-btn" style="padding: 6px 24px; background: url('@/assets/kenney_pixel-ui-pack/ancient/list.png') no-repeat center/cover; color: #222; border: none;">保存</button>
          </div>
          <div v-if="diarySaved" style="color: #67c23a; font-size: 13px; margin-top: 4px;">已保存！</div>
        </div>
        <div class="pixel-inlay-card tan" style="margin-bottom: 0;">
          <div style="display: flex; flex-direction: row; gap: 24px;">
            <div style="flex: 2; display: flex; flex-direction: column;">
              <h3 class="pixel-title" style="margin-bottom: 16px; color: #6b4f3b;">阅读计划对话</h3>
              <div class="chat-panel">
                <div class="chat-messages" ref="chatMessagesRef">
                  <div
                    v-for="(msg, idx) in messages"
                    :key="idx"
                    :class="['chat-row', msg.role === 'user' ? 'chat-row-user' : 'chat-row-assistant']"
                  >
                    <template v-if="msg.role === 'user'">
                      <div class="chat-meta-user">
                        <img :src="userImg" alt="user" class="chat-avatar" />
                        <span class="bubble-label">我</span>
                      </div>
                      <div class="chat-bubble bubble-user">
                        <span>{{ msg.content }}</span>
                      </div>
                    </template>
                    <template v-else>
                      <div class="chat-meta-assistant">
                        <img :src="robotImg" alt="robot" class="chat-avatar" />
                        <span class="bubble-label">助手</span>
                      </div>
                      <div class="chat-bubble bubble-assistant">
                        <span v-html="marked(msg.content)"></span>
                      </div>
                    </template>
                  </div>
                </div>
                <div class="chat-input-row">
                  <input v-model="chatInput" @keyup.enter="sendChat" placeholder="和助手聊聊你的阅读计划..." class="pixel-input" />
                  <button @click="sendChat" class="pixel-btn send-btn">发送</button>
                </div>
              </div>
            </div>
            <div style="flex: none; width: 150px; border-left: 1px solid #eee; padding-left: 8px; display: flex; flex-direction: column;">
              <h4 class="pixel-title" style="margin-bottom: 8px; color: #6b4f3b;">历史对话</h4>
              <div style="margin-bottom: 8px; display: flex; gap: 4px;">
                <input v-model="newConversationTitle" placeholder="新会话标题..." class="pixel-btn" style="width: 70px; padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; font-size: 12px;" />
                <button @click="createConversation" class="pixel-btn" style="padding: 4px 8px; border-radius: 6px; background: #67c23a; color: #fff; border: none; font-size: 12px;">新建</button>
              </div>
              <ul style="list-style: none; padding: 0; margin: 0; max-height: 320px; overflow-y: auto; border-radius: 8px; border: 1.5px solid #e6cfa7; background: #fffbe6;">
                <li
                  v-for="c in conversations"
                  :key="c.id"
                  @click="selectConversation(c.id)"
                  class="conversation-item"
                  :class="{ active: c.id === currentConversationId }"
                >
                  <div class="conv-main">
                    <div>{{ c.title }}</div>
                    <div class="conv-time">{{ dayjs(c.updated_at).format('YYYY-MM-DD HH:mm') }}</div>
                  </div>
                  <button
                    class="delete-btn"
                    @click.stop="onDeleteConversation(c.id)"
                    title="删除"
                  >🗑️</button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- AI建议新计划弹窗样式同样可用pixel-inlay-card -->
    <div v-if="showPlanDialog"
         style="position: fixed; left: 0; top: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.25); z-index: 9999; display: flex; align-items: center; justify-content: center;">
      <div class="pixel-inlay-card tan plan-dialog-bg">
        <h3 class="pixel-title" style="margin-bottom: 16px;">AI建议的新阅读计划</h3>
        <div v-if="pendingPlanObj">
          <div style="font-weight: bold; margin-bottom: 8px;">书名：{{ pendingPlanObj.book }}</div>
          <div style="font-weight: bold; margin-bottom: 8px;">总天数：{{ pendingPlanObj.total_days }}</div>
          <div style="font-weight: bold; margin-bottom: 8px;">每日任务：</div>
          <ul style="margin-left: 16px;">
            <li v-for="item in pendingPlanObj.daily_plan" :key="item.day" style="margin-bottom: 6px;">
              <b>第{{ item.day }}天：</b>{{ item.task }}
            </li>
          </ul>
          <div v-if="pendingPlanObj.raw">AI原始内容：{{ pendingPlanObj.raw }}</div>
        </div>
        <div style="margin-top: 24px; display: flex; gap: 16px; justify-content: flex-end;">
          <button @click="onAcceptNewPlan" class="pixel-btn" style="padding: 8px 24px; border-radius: 8px; background: #67c23a; color: #fff; border: none; font-size: 16px;">同意</button>
          <button @click="onRejectNewPlan" class="pixel-btn" style="padding: 8px 24px; border-radius: 8px; background: #ccc; color: #fff; border: none; font-size: 16px;">不同意</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import axios from 'axios'
import dayjs from 'dayjs'
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter'
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore'
import PixelEmotionBar from './PixelEmotionBar.vue'
import calendarBg from '@/assets/calendar-bg.png'
import motionBg from '@/assets/motion_bg.png'
import diaryBg from '@/assets/diary_bg.png'
import robotImg from '@/assets/robot.png'
import userImg from '@/assets/user.png'
//import brownInlay from '@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown_inlay.png'
//import blueBtn from '@/assets/kenney_pixel-ui-pack/9-Slice/Colored/blue.png'
//import blueBtnPressed from '@/assets/kenney_pixel-ui-pack/9-Slice/Colored/blue_pressed.png'
// import brownPng from '@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown.png'
import { marked } from 'marked'

dayjs.extend(isSameOrAfter)
dayjs.extend(isSameOrBefore)
function getMonthDays(year, month) {
  const date = new Date(year, month, 1);
  const days = [];
  while (date.getMonth() === month) {
    days.push(new Date(date));
    date.setDate(date.getDate() + 1);
  }
  return days;
}

const today = new Date();
const yyyy = today.getFullYear();
const mm = today.getMonth();


const calendarRows = ref([])
const conversations = ref([])
const currentConversationId = ref(null)
const messages = ref([])
const newConversationTitle = ref('')

const plans = ref([])
const loading = ref(false)
const error = ref('')
// 用户ID统一为test_user，防止因user_id不一致导致后端查不到计划或会话
const userId = 'test_user';

const selectedBook = ref('')
const selectedPlanObj = ref(null)
const selectedDay = ref(null)
const selectedDayTask = ref('')
const diaryText = ref('')
const diarySaved = ref(false)
const editMode = ref(false)
const editPlanObj = ref({
  book: '',
  start_date: '',
  end_date: '',
  total_days: 0,
  daily_plan: [],
})
const chatInput = ref('')
const dailyStatus = ref({})
const selectedDayNum = ref(null);
const diaryEditMode = ref(false);
const showPlanDialog = ref(false);
const pendingPlanObj = ref(null);
const autoDiaryTip = ref(''); // 页面内温和提示
const chatMessagesRef = ref(null);

// 自动滚动到底部
watch(messages, async () => {
  await nextTick();
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
  }
});

// 书籍下拉框去重
const uniqueBooks = computed(() => {
  const set = new Set();
  plans.value.forEach(plan => {
    const book = parsePlanContent(plan.plan_content)?.book;
    if (book) set.add(book);
  });
  return Array.from(set);
});

async function onAcceptNewPlan() {
  if (!pendingPlanObj.value) return;
  await axios.post('/api/chatbot/update_plan/', {
    user_id: userId,
    plan_id: Number(selectedPlanObj.value.id),
    plan_content: JSON.stringify(pendingPlanObj.value)
  });
  showPlanDialog.value = false;
  // 等待后端写入
  await new Promise(r => setTimeout(r, 500));
  // 强制刷新计划和打卡数据
  await fetchMyPlans();
  await fetchDailyStatus();
  // 重置选中日期和任务
  selectedDay.value = null;
  selectedDayTask.value = '';
  // 在对话区插入一句简短提示
  messages.value.push({ role: 'assistant', content: '已为你更新新计划！' });
  await axios.post('/api/chatbot/messages/', {
    conversation_id: currentConversationId.value,
    role: 'assistant',
    content: '已为你更新新计划！'
  });
  pendingPlanObj.value = null;
  await refreshDiary(); // 新增：同意新计划后刷新日记
}
function onRejectNewPlan() {
  showPlanDialog.value = false;
  // 用户不同意，助手继续正常对话
  messages.value.push({ role: 'assistant', content: '好的，我们继续聊聊其他话题吧！' });
  axios.post('/api/chatbot/messages/', {
    conversation_id: currentConversationId.value,
    role: 'assistant',
    content: '好的，我们继续聊聊其他话题吧！'
  });
  pendingPlanObj.value = null;
}



// 重写sendChat，先处理弹窗
async function sendChat() {
  if (!chatInput.value || !currentConversationId.value) return;
  const userMsg = chatInput.value;
  chatInput.value = '';
  messages.value.push({ role: 'user', content: userMsg });
  await axios.post('/api/chatbot/messages/', {
    conversation_id: currentConversationId.value,
    role: 'user',
    content: userMsg
  });
  // 调用AI接口获取回复
  axios.post('/api/chatbot/direct_chat_with_diary/', {
    user_id: userId,
    plan_id: Number(selectedPlanObj.value.id),
    message: userMsg,
    current_book: selectedPlanObj.value ? selectedPlanObj.value.book : '',
    current_plan: selectedPlanObj.value ? JSON.stringify(selectedPlanObj.value) : ''
  }).then(async res => {
    // 检查是否有 new_plan
    if (res.data.new_plan) {
      let planObj = null;
      try {
        planObj = typeof res.data.new_plan === 'string' ? JSON.parse(res.data.new_plan) : res.data.new_plan;
      } catch (e) {
        console.error('解析new_plan失败:', e);
      }
      if (planObj && planObj.book) {
        // 弹窗展示新计划内容，等待用户同意
        showPlanDialog.value = true;
        pendingPlanObj.value = planObj;
        // 如果有引导语，显示在对话区
        if (res.data.reply && res.data.reply.trim()) {
          messages.value.push({ role: 'assistant', content: res.data.reply });
          await axios.post('/api/chatbot/messages/', {
            conversation_id: currentConversationId.value,
            role: 'assistant',
            content: res.data.reply
          });
        }
        await refreshDiary(); // 新增：AI建议新计划后也刷新日记
        return; // 阻止后续处理，因为已经弹窗了
      }
    }
    // 只显示非JSON的助手回复
    if (res.data.reply && !isJsonLike(res.data.reply)) {
      messages.value.push({ role: 'assistant', content: res.data.reply });
      await axios.post('/api/chatbot/messages/', {
        conversation_id: currentConversationId.value,
        role: 'assistant',
        content: res.data.reply
      });
    }
    await refreshDiary(); // 新增：AI普通回复后刷新日记
  }).catch(e => {
    messages.value.push({ role: 'assistant', content: '对话出错：' + (e.response?.data?.error || e.message) });
    refreshDiary(); // 新增：对话出错也刷新日记
  });
}

// 情绪数据
const emotionData = ref([])
async function fetchEmotionData() {
  if (!userId || !selectedBook.value) return;
  try {
    let url = `/api/chatbot/emotion_curve/?user_id=${encodeURIComponent(userId)}`
    if (selectedBook.value) {
      url += `&book=${encodeURIComponent(selectedBook.value)}`
    }
    const res = await axios.get(url)
    emotionData.value = res.data
  } catch (e) {
    emotionData.value = []
  }
}
watch([selectedBook], fetchEmotionData, { immediate: true })

async function fetchMyPlans() {
  loading.value = true
  error.value = ''
  try {
    const res = await axios.post('/api/chatbot/my_plans/', {
      user_id: userId
    })
    plans.value = res.data.plans
    // 优先选中激活计划
    let activePlan = plans.value.find(p => p.is_active)
    if (!activePlan && plans.value.length) activePlan = plans.value[0]
    if (activePlan && activePlan.plan_content) {
      const planObj = parsePlanContent(activePlan.plan_content)
      selectedBook.value = planObj.book
      selectedPlanObj.value = {
        ...planObj,
        id: activePlan.id,
        plan_id: activePlan.id,
        book: activePlan.book || planObj?.book,
        start_date: activePlan.start_date,
        end_date: activePlan.end_date,
        is_active: activePlan.is_active,
      }
      editPlanObj.value = JSON.parse(JSON.stringify(selectedPlanObj.value))
      // 关键：计划变更后立即刷新打卡状态
      await fetchDailyStatus();
      fetchConversations();
    }
  } catch (e) {
    error.value = '获取失败：' + (e.response?.data?.error || e.message)
  } finally {
    loading.value = false
  }
}

function buildCalendar() {
  const monthDays = getMonthDays(yyyy, mm);
  const firstDay = monthDays[0].getDay();
  const rows = [];
  let row = Array(firstDay).fill({ day: '', date: '' });
  monthDays.forEach(d => {
    row.push({ day: d.getDate(), date: dayjs(d).format('YYYY-MM-DD') });
    if (row.length === 7) {
      rows.push(row);
      row = [];
    }
  });
  if (row.length) rows.push([...row, ...Array(7-row.length).fill({ day: '', date: '' })]);
  calendarRows.value = rows;
}

function parsePlanContent(planContent) {
  let text = planContent.trim();
  text = text.replace(/^```json/, '').replace(/^```/, '').replace(/```$/, '').replace(/^json/, '').trim();
  let obj = null;
  try {
    obj = JSON.parse(text);
  } catch (e) {
    return null;
  }
  // 补全字段
  if (!obj.book) obj.book = '';
  if (!obj.start_date) obj.start_date = '';
  if (!obj.end_date && obj.start_date && obj.total_days) {
    try {
      const start = dayjs(obj.start_date);
      obj.end_date = start.add(obj.total_days - 1, 'day').format('YYYY-MM-DD');
    } catch (e) { obj.end_date = ''; }
  }
  if (!obj.total_days && obj.daily_plan) obj.total_days = obj.daily_plan.length;
  if (!Array.isArray(obj.daily_plan)) obj.daily_plan = [];
  obj.daily_plan.forEach((item, idx) => {
    if (!item.day) item.day = idx + 1;
    if (!item.task) item.task = '';
  });
  return obj;
}

function onSelectBook() {
  const plan = plans.value.find(p => p.plan_content && parsePlanContent(p.plan_content)?.book === selectedBook.value);
  if (plan) {
    let planObj = parsePlanContent(plan.plan_content);
    selectedPlanObj.value = {
      ...planObj,
      id: plan.id,
      plan_id: plan.id,
      book: plan.book || planObj?.book,
      start_date: plan.start_date,
      end_date: plan.end_date,
      is_active: plan.is_active,
    };
    selectedDay.value = null;
    selectedDayTask.value = '';
    editMode.value = false;
    editPlanObj.value = JSON.parse(JSON.stringify(selectedPlanObj.value));
    fetchDailyStatus();
  } else {
    selectedPlanObj.value = null;
    selectedDay.value = null;
    selectedDayTask.value = '';
    editMode.value = false;
    editPlanObj.value = { book: '', total_days: 0, daily_plan: [] };
  }
}

function getTaskForDayByDate(dateStr) {
  if (!selectedPlanObj.value) return '';
  const start = dayjs(selectedPlanObj.value.start_date);
  const d = dayjs(dateStr);
  const dayIndex = d.diff(start, 'day') + 1;
  const taskObj = selectedPlanObj.value.daily_plan.find(d => d.day === dayIndex);
  return taskObj ? taskObj.task : '';
}

async function fetchDailyStatus() {
  console.log('fetchDailyStatus plan_id:', selectedPlanObj.value && selectedPlanObj.value.id, selectedPlanObj.value);
  if (!selectedPlanObj.value || !selectedPlanObj.value.start_date) return;
  const start = dayjs(selectedPlanObj.value.start_date).startOf('month').format('YYYY-MM-DD');
  const end = dayjs(selectedPlanObj.value.start_date).endOf('month').format('YYYY-MM-DD');
  try {
    const res = await axios.post('/api/chatbot/get_daily_status/', {
      user_id: userId,
      book: selectedPlanObj.value.book,
      start_date: start,
      end_date: end
    });
    dailyStatus.value = res.data.status || {};
  } catch (e) {
    dailyStatus.value = {};
  }
}

function isInPlanRange(dateStr) {
  if (!selectedPlanObj.value) return false;
  const start = dayjs(selectedPlanObj.value.start_date);
  const end = dayjs(selectedPlanObj.value.end_date);
  const d = dayjs(dateStr);
  return d.isSameOrAfter(start) && d.isSameOrBefore(end);
}

async function selectDate(date, dayNum) {
  const dateStr = dayjs(date).format('YYYY-MM-DD');
  if (!date || !selectedPlanObj.value || !isInPlanRange(dateStr)) return;

  const isChecked = !!dailyStatus.value[dateStr];
  const todayStr = dayjs().format('YYYY-MM-DD');
  const isToday = dateStr === todayStr;

  // 只允许：已打卡的（绿色）、今天（蓝色）可点
  if (!(isChecked || isToday)) return;

  selectedDay.value = dateStr;
  selectedDayNum.value = dayNum;
  selectedDayTask.value = getTaskForDayByDate(dateStr);
  try {
    const res = await axios.post('/api/chatbot/get_diary/', {
      user_id: userId,
      plan_id: Number(selectedPlanObj.value.id),
      date: dateStr,
      book: selectedPlanObj.value.book
    });
    console.log('get_diary返回', res.data);
    // 优先展示auto_diary
    if (res.data.auto_diary) {
      diaryText.value = res.data.auto_diary;
      diaryEditMode.value = true;
      autoDiaryTip.value = '已为你自动生成日记，可编辑保存';
      setTimeout(() => { autoDiaryTip.value = ''; }, 1500);
    } else {
      diaryText.value = res.data.remark || '';
      diaryEditMode.value = false;
    }
  } catch (e) {
    diaryText.value = '';
    diaryEditMode.value = false;
  }
  // 只允许今天打卡
  if (isToday && !dailyStatus.value[dateStr]) {
    await axios.post('/api/chatbot/mark_day/', {
      user_id: userId,
      plan_id: Number(selectedPlanObj.value.id),
      date: dateStr,
      book: selectedPlanObj.value.book,
      actual_progress: '手动打卡'
    });
    await fetchDailyStatus();
    // 打卡后强制刷新日记内容
    try {
      const res2 = await axios.post('/api/chatbot/get_diary/', {
        user_id: userId,
        plan_id: Number(selectedPlanObj.value.id),
        date: dateStr,
        book: selectedPlanObj.value.book
      });
      console.log('打卡后get_diary返回', res2.data);
      diaryText.value = res2.data.remark || '';
      diaryEditMode.value = false;
    } catch (e) {
      //nothing
    }
  }

  // 切换到当天的会话（不再自动新建，只切换currentConversationId）
  let conv = conversations.value.find(c => dayjs(c.created_at).format('YYYY-MM-DD') === dateStr);
  if (conv) {
    currentConversationId.value = conv.id;
    fetchMessages(conv.id);
  } else {
    currentConversationId.value = null;
    messages.value = [];
  }
}

function onEditDiary() {
  diaryEditMode.value = true;
}

async function saveDiary() {
  console.log('saveDiary plan_id:', selectedPlanObj.value && selectedPlanObj.value.id, selectedPlanObj.value);
  const todayStr = dayjs().format('YYYY-MM-DD');
  if (!selectedDay.value || selectedDay.value !== todayStr) return;
  await axios.post('/api/chatbot/mark_day/', {
    user_id: userId,
    plan_id: Number(selectedPlanObj.value.id),
    date: selectedDay.value,
    book: selectedPlanObj.value.book,
    actual_progress: '日记打卡',
    remark: diaryText.value
  });
  await fetchDailyStatus();
  // 保存后强制刷新日记内容
  try {
    const res = await axios.post('/api/chatbot/get_diary/', {
      user_id: userId,
      plan_id: Number(selectedPlanObj.value.id),
      date: selectedDay.value,
      book: selectedPlanObj.value.book
    });
    console.log('保存后get_diary返回', res.data);
    diaryText.value = res.data.remark || '';
    diaryEditMode.value = false;
  } catch (e) {
    //nothing
  }
  diarySaved.value = true;
  setTimeout(() => { diarySaved.value = false }, 1200);
  await refreshDiary(); // 新增：保存日记后刷新日记
}

function saveEditPlan() {
  if (!editPlanObj.value.start_date) {
    editPlanObj.value.start_date = dayjs().format('YYYY-MM-DD');
  }
  selectedPlanObj.value = JSON.parse(JSON.stringify(editPlanObj.value));
  editMode.value = false;
  // 可扩展为持久化到后端
}

// function msgStyle(role) {
//   return {
//     margin: '8px 0',
//     textAlign: role === 'user' ? 'right' : 'left',
//   }
// }

function isJsonLike(str) {
  // 简单判断是否为json
  if (!str) return false;
  const s = str.trim();
  return s.startsWith('{') || s.startsWith('```json') || s.startsWith('"book"') || s.startsWith('book');
}

// 获取会话列表
async function fetchConversations() {
  if (!selectedPlanObj.value) return;
  const res = await axios.get('/api/chatbot/conversations/', {
    params: { user_id: userId, book: selectedPlanObj.value.book }
  });
  conversations.value = res.data.conversations;
  if (conversations.value.length && !currentConversationId.value) {
    currentConversationId.value = conversations.value[0].id;
    fetchMessages(currentConversationId.value);
  }
}

// 获取消息
async function fetchMessages(conversationId) {
  const res = await axios.get('/api/chatbot/messages/', {
    params: { conversation_id: conversationId }
  });
  messages.value = res.data.messages;
}

// 新建会话时带上date字段
async function createConversation() {
  if (!selectedPlanObj.value || !selectedPlanObj.value.id) {
    alert('请先新建或选择一个有效的阅读计划，再开始对话！');
    return;
  }
  if (!newConversationTitle.value.trim()) {
    alert('请输入会话标题');
    return;
  }
  if (!selectedPlanObj.value.book) {
    alert('请选择书籍');
    return;
  }
  let dateToUse = selectedDay.value;
  if (!dateToUse) {
    dateToUse = dayjs().format('YYYY-MM-DD');
  }
  // plan_id 兜底
  let planIdToUse = selectedPlanObj.value.id || selectedPlanObj.value.plan_id || null;
  if (!planIdToUse) {
    alert('计划ID缺失，无法新建会话');
    return;
  }
  const params = {
    user_id: userId,
    book: selectedPlanObj.value.book,
    title: newConversationTitle.value.trim(),
    date: dateToUse,
    plan_id: planIdToUse
  };
  console.log('新建会话参数', params);
  try {
    const res = await axios.post('/api/chatbot/conversations/', params);
    newConversationTitle.value = '';
    await fetchConversations();
    currentConversationId.value = res.data.id;
    messages.value = [];
  } catch (e) {
    alert('新建会话失败：' + (e.response?.data?.error || e.message));
  }
}

// 切换会话
function selectConversation(id) {
  currentConversationId.value = id;
  fetchMessages(id);
}

async function onDeleteConversation(id) {
  if (!id) return;
  if (!window.confirm('确定要删除该会话吗？')) return;
  try {
    await axios.delete(`/api/chatbot/conversations/${id}/`);
    await fetchConversations();
    if (currentConversationId.value === id) {
      currentConversationId.value = null;
      messages.value = [];
    }
  } catch (e) {
    alert('删除失败：' + (e.response?.data?.error || e.message));
  }
}

// 发送消息
// 切换计划时自动加载会话列表
watch(selectedPlanObj, () => {
  fetchDailyStatus();
  fetchConversations();
  currentConversationId.value = null;
  messages.value = [];
});

onMounted(() => {
  buildCalendar();
  fetchMyPlans().then(() => {
    if (plans.value.length) {
      const firstPlan = plans.value[0];
      if (firstPlan && firstPlan.plan_content) {
        const planObj = parsePlanContent(firstPlan.plan_content);
        selectedBook.value = planObj.book;
        selectedPlanObj.value = {
          ...planObj,
          id: firstPlan.id,
          plan_id: firstPlan.id,
          book: firstPlan.book || planObj?.book,
          start_date: firstPlan.start_date,
          end_date: firstPlan.end_date,
          is_active: firstPlan.is_active,
        };
        editPlanObj.value = JSON.parse(JSON.stringify(selectedPlanObj.value));
        fetchDailyStatus();
        fetchConversations();
        // 自动选中今天
        const todayStr = dayjs().format('YYYY-MM-DD');
        const todayNum = dayjs().date();
        selectDate(todayStr, todayNum);
      }
    }
  });
});

function calendarCellStyle(date) {
  const dateStr = dayjs(date).format('YYYY-MM-DD');
  if (!date || !selectedPlanObj.value || !isInPlanRange(dateStr)) {
    // 计划外
    return {
      padding: '8px', border: '1px solid #eee', background: '#fff', color: '#ccc', cursor: 'default', minWidth: '40px', minHeight: '40px', textAlign: 'center', borderRadius: '6px'
    };
  }
  const isChecked = !!dailyStatus.value[dateStr];
  const todayStr = dayjs().format('YYYY-MM-DD');
  const isToday = dateStr === todayStr;
  const isFuture = dayjs(dateStr).isAfter(todayStr);
  const isPast = dayjs(dateStr).isBefore(todayStr);

  if (isChecked) {
    // 已打卡：绿色
    return {
      padding: '8px', border: '2px solid #52c41a', background: '#f6ffed', color: '#52c41a', cursor: 'pointer', minWidth: '40px', minHeight: '40px', textAlign: 'center', borderRadius: '6px', fontWeight: 'bold'
    };
  } else if (isToday) {
    // 今天未打卡：蓝色
    return {
      padding: '8px', border: '2px solid #409eff', background: '#e6f7ff', color: '#409eff', cursor: 'pointer', minWidth: '40px', minHeight: '40px', textAlign: 'center', borderRadius: '6px', fontWeight: 'bold'
    };
  } else if (isFuture) {
    // 未来未打卡：蓝色，不可点
    return {
      padding: '8px', border: '2px solid #409eff', background: '#e6f7ff', color: '#409eff', cursor: 'not-allowed', minWidth: '40px', minHeight: '40px', textAlign: 'center', borderRadius: '6px'
    };
  } else if (isPast) {
    // 过去未打卡：灰色
    return {
      padding: '8px', border: '1px solid #eee', background: '#fafafa', color: '#ccc', cursor: 'not-allowed', minWidth: '40px', minHeight: '40px', textAlign: 'center', borderRadius: '6px'
    };
  }
  // 兜底
  return {
    padding: '8px', border: '1px solid #eee', background: '#fff', color: '#ccc', cursor: 'default', minWidth: '40px', minHeight: '40px', textAlign: 'center', borderRadius: '6px'
  };
}

function isPlanDay(dateStr) {
  if (!selectedPlanObj.value || !selectedPlanObj.value.start_date) return false;
  const start = dayjs(selectedPlanObj.value.start_date);
  const d = dayjs(dateStr);
  const dayIndex = d.diff(start, 'day') + 1;
  return dayIndex >= 1 && dayIndex <= selectedPlanObj.value.total_days;
}

// 新增：刷新日记内容
async function refreshDiary() {
  if (!selectedPlanObj.value || !selectedDay.value) return;
  try {
    const res = await axios.post('/api/chatbot/get_diary/', {
      user_id: userId,
      plan_id: Number(selectedPlanObj.value.id),
      date: selectedDay.value,
      book: selectedPlanObj.value.book
    });
    diaryText.value = res.data.auto_diary || res.data.remark || '';
    diaryEditMode.value = !!res.data.auto_diary;
  } catch (e) {
    diaryText.value = '';
    diaryEditMode.value = false;
  }
}
</script>

<style scoped>
::-webkit-scrollbar { width: 6px; background: #f5f6fa; }
::-webkit-scrollbar-thumb { background: #eee; border-radius: 3px; }
.pixel-card {
  background: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/brown.png') repeat;
  background-size: cover;
  border-radius: 8px;
  padding: 24px;
  color: #333;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  box-shadow: 0 2px 8px rgba(75, 46, 5, 0.08);
}
.pixel-tan-card {
  background: #cbb98a;
  border: 2px solid #b48a78;
  border-radius: 14px;
  box-shadow: 0 4px 16px rgba(180,138,120,0.13), 0 1.5px 0 #e6cfa7 inset;
}
.pixel-calendar-card {
  border: 4px solid transparent;
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/tan.png') 8 fill stretch;
  background: none;
  border-radius: 0;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  padding: 24px;
  margin-bottom: 24px;
}

.pixel-calendar-cell {
  border: 4px solid transparent;
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Colored/green.png') 8 fill stretch;
  background: #fff;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  color: #333;
  min-width: 40px;
  min-height: 40px;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
}
.pixel-calendar-cell.selected {
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Colored/blue_pressed.png') 8 fill stretch;
  background: #e6f7ff;
  color: #409eff;
}
.pixel-plan-card {
  border: 4px solid transparent;
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/white_inlay.png') 8 fill stretch;
  background: none;
  border-radius: 0;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  padding: 18px;
  margin: 12px 0;
  color: #333;
}

.pixel-bullet-li {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
}
.pixel-bullet {
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-right: 8px;
  background: url('@/assets/kenney_pixel-ui-pack/Spritesheet/UIpackSheet_transparent.png') no-repeat;
  background-size: 256px 256px; /* 取决于 Spritesheet 实际尺寸 */
  background-position: -32px -16px; /* 这里举例，需根据实际小图标位置调整 */
}
.pixel-inlay-card {

  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 16px;
  
}
.pixel-inlay-card.tan {

}
.chat-bubble {
  max-width: 80%;
  margin: 8px 0;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 15px;
  word-break: break-all;
  box-shadow: 0 1px 2px #eee;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  letter-spacing: 1.5px;
}
.bubble-user {
  background: #e6f7ff;
  color: #409eff;
  margin-left: auto;
  border: 2px solid #b3d8ff;
  text-align: right;
}
.bubble-assistant {
  background: #f6ffed;
  color: #52c41a;
  margin-right: auto;
  border: 2px solid #b7eb8f;
  text-align: left;
}
.bubble-label {
  font-weight: bold;
  margin-right: 4px;
}
.chat-panel {
  background: #fffbe6;
  border: 4px solid transparent;
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/white_inlay.png') 8 fill stretch;
  border-radius: 10px;
  box-shadow: 0 2px 8px #e6cfa7;
  padding: 18px 18px 12px 18px;
  display: flex;
  flex-direction: column;
  height: 320px;
  min-width: 0;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 10px;
}
.chat-input-row {
  display: flex;
  gap: 8px;
}
.pixel-input {
  flex: 1;
  padding: 8px;
  border: 2px solid #b48a78;
  border-radius: 6px;
  background: #fff;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  font-size: 15px;
}
.send-btn {
  min-width: 64px;
  background: #409eff;
  color: #fff;
  border: 2px solid #2766a7;
  border-radius: 6px;
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
  font-size: 15px;
  transition: background 0.2s;
}
.send-btn:hover {
  background: #66b1ff;
}
.pixel-inlay-card {
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 16px;
}
.pixel-card-title {
  font-family: 'Zpix', 'PixelFont', monospace;
  font-size: 18px;
  color: #fff;
  margin-bottom: 10px;
  letter-spacing: 1px;
}
.pixel-btn.pixel-blue {
  background: url(~@/assets/kenney_pixel-ui-pack/9-Slice/Colored/blue.png) no-repeat center/cover;
  font-family: 'Zpix', 'PixelFont', monospace;
  color: #fff;
  font-size: 16px;
  border: none;
  outline: 2px solid #2a3e7b;
  padding: 8px 24px;
  cursor: pointer;
  box-shadow: 0 2px #1a2d5a;
  transition: filter 0.1s, transform 0.1s;
}
.pixel-btn.pixel-blue:active {
  background: url(~@/assets/kenney_pixel-ui-pack/9-Slice/Colored/blue_pressed.png) no-repeat center/cover;
  filter: brightness(0.95);
  transform: translateY(2px);
}
.note-paper {
  background: url('@/assets/plan_bg.png') center -150px / 150% 120% no-repeat;
  border-radius: 12px 16px 14px 10px;
  padding: 48px 22px 32px 32px;
  margin: 0 0 12px 0;
  position: relative;
  min-width: 360px;
  min-height: 720px;
  font-family: 'Zpix', 'PixelFont', '微软雅黑', monospace;
  box-sizing: border-box;
}
.note-paper::before {
  content: '';
  display: block;
  position: absolute;
  top: -14px;
  left: 32px;
  width: 100px;
  height: 18px;

  z-index: 2;
}
.note-paper b, .note-paper strong {
  color: #6b4f3b;
  font-weight: bold;
}
.note-paper li {
  margin-bottom: 6px;
}
.chat-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}
.chat-row-user {
  flex-direction: row-reverse;
  justify-content: flex-end;
}
.chat-row-assistant {
  flex-direction: row;
  justify-content: flex-start;
}
.chat-meta-user, .chat-meta-assistant {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 40px;
}
.chat-avatar {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: #fff;
  border: 1.5px solid #e0d3b8;
}
.bubble-label {
  font-weight: bold;
  margin: 0 4px;
}
.conversation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px;
  border-radius: 6px;
  margin-bottom: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  position: relative;
  transition: background 0.2s;
}
.conversation-item.active {
  background: #e6f7ff;
  font-weight: bold;
}
.conversation-item .delete-btn {
  display: none;
  background: none;
  border: none;
  color: #d9534f;
  font-size: 16px;
  cursor: pointer;
  margin-left: 8px;
  transition: color 0.2s;
}
.conversation-item:hover .delete-btn {
  display: inline;
}
.conversation-item .delete-btn:hover {
  color: #ff2d55;
  text-shadow: 0 0 2px #fff;
}
.conv-main {
  flex: 1;
  min-width: 0;
}
.conv-time {
  font-size: 11px;
  color: #888;
}
.plan-dialog-bg {
  background: #fffbe6;
  border: 4px solid #b48a78;
  border-radius: 18px;
  box-shadow: 0 8px 32px #b48a78;
  min-width: 400px;
  max-width: 90vw;
  padding: 32px;
}
</style> 