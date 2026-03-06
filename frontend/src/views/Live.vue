<template>
  <div class="live-page">
    <el-card>
      <template #header>
        <span>直播监听</span>
      </template>

      <el-form inline>
        <el-form-item label="房间号">
          <el-input v-model="roomId" placeholder="输入直播间房间号" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startListen" :loading="listening">开始监听</el-button>
          <el-button @click="stopListen" :disabled="!listening">停止监听</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>实时弹幕</span>
      </template>
      <div class="danmu-container" ref="danmuContainer">
        <div v-for="(item, index) in danmuList" :key="index" class="danmu-item">
          <span class="time">{{ item.time }}</span>
          <span class="user">{{ item.user }}:</span>
          <span class="content">{{ item.content }}</span>
        </div>
        <div v-if="!danmuList.length" class="empty">暂无弹幕数据</div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const roomId = ref('')
const listening = ref(false)
const danmuList = ref([])
let ws = null

const formatTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN')
}

const startListen = () => {
  if (!roomId.value) return

  const wsUrl = `ws://${location.host}/ws/live/${roomId.value}`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    listening.value = true
    addDanmu({ user: '系统', content: '连接成功', time: formatTime() })
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      addDanmu({
        user: data.user || '未知',
        content: data.content || '',
        time: formatTime()
      })
    } catch (e) {}
  }

  ws.onclose = () => {
    listening.value = false
    addDanmu({ user: '系统', content: '连接已断开', time: formatTime() })
  }

  ws.onerror = () => {
    listening.value = false
  }
}

const stopListen = () => {
  if (ws) {
    ws.close()
    ws = null
  }
  listening.value = false
}

const addDanmu = (item) => {
  danmuList.value.push(item)
  if (danmuList.value.length > 100) {
    danmuList.value.shift()
  }
}

onUnmounted(() => {
  stopListen()
})
</script>

<style scoped>
.danmu-container {
  height: 400px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.danmu-item {
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.danmu-item .time {
  color: #999;
  margin-right: 10px;
  font-size: 12px;
}

.danmu-item .user {
  color: #409eff;
  font-weight: bold;
  margin-right: 5px;
}

.danmu-item .content {
  color: #333;
}

.empty {
  text-align: center;
  color: #999;
  padding: 40px;
}
</style>
