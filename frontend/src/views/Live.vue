<template>
  <div class="live-page">
    <!-- 输入区域 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>直播监听</span>
          <el-tag v-if="listening" type="success" size="small">监听中</el-tag>
        </div>
      </template>

      <!-- Tab 切换输入方式 -->
      <el-tabs v-model="inputMode" class="input-tabs">
        <el-tab-pane label="链接/房间号" name="url">
          <el-input
            v-model="inputUrl"
            placeholder="粘贴直播间链接或输入房间号，如：https://live.douyin.com/81804234251 或 81804234251"
            size="large"
            clearable
            @keyup.enter="previewRoom"
          >
            <template #prefix>
              <el-icon><Link /></el-icon>
            </template>
            <template #append>
              <el-button @click="previewRoom" :loading="previewing">预览</el-button>
            </template>
          </el-input>
        </el-tab-pane>

        <el-tab-pane label="搜索主播" name="search">
          <el-input
            v-model="searchKeyword"
            placeholder="输入主播昵称搜索直播间"
            size="large"
            clearable
            @keyup.enter="searchLive"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button @click="searchLive" :loading="searching">搜索</el-button>
            </template>
          </el-input>
        </el-tab-pane>
      </el-tabs>

      <!-- 直播间预览信息 -->
      <div v-if="previewData" class="preview-box">
        <div class="preview-content">
          <div class="preview-info">
            <h3>{{ previewData.room_title || '未命名直播间' }}</h3>
            <div class="preview-meta">
              <el-tag :type="previewData.is_living ? 'success' : 'info'" size="small">
                {{ previewData.status_text }}
              </el-tag>
              <span class="room-id">房间号: {{ previewData.room_id }}</span>
            </div>
          </div>
          <div class="preview-actions">
            <el-button
              type="primary"
              size="large"
              @click="startListen"
              :loading="starting"
              :disabled="!previewData.is_living"
            >
              {{ previewData.is_living ? '开始监听' : '未开播' }}
            </el-button>
            <el-button v-if="listening" @click="stopListen" :loading="stopping" size="large">
              停止监听
            </el-button>
          </div>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0" class="search-results">
        <div class="search-header">
          <span>搜索结果 ({{ searchResults.length }})</span>
          <el-button text @click="searchResults = []">清除</el-button>
        </div>
        <div class="live-cards">
          <div
            v-for="item in searchResults"
            :key="item.room_id"
            class="live-card"
            :class="{ active: selectedRoom?.room_id === item.room_id }"
            @click="selectRoom(item)"
          >
            <div class="live-cover">
              <img :src="item.cover || '/default-cover.jpg'" alt="cover" />
              <div class="live-badge" :class="{ living: item.is_living }">
                {{ item.is_living ? '直播中' : '未开播' }}
              </div>
              <div v-if="item.is_living" class="viewer-count">
                <el-icon><View /></el-icon>
                {{ formatNumber(item.viewer_count) }}
              </div>
            </div>
            <div class="live-info">
              <div class="live-title">{{ item.room_title || '未命名' }}</div>
              <div class="live-owner">
                <img :src="item.owner.avatar || '/default-avatar.jpg'" class="avatar" />
                <span>{{ item.owner.nickname }}</span>
                <span class="followers">{{ formatNumber(item.owner.follower_count) }} 粉丝</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 统计信息 -->
      <div v-if="listening && stats" class="stats-row">
        <el-tag>弹幕: {{ stats.danmu_count || 0 }}</el-tag>
        <el-tag type="warning">礼物: {{ stats.gift_count || 0 }}</el-tag>
        <el-tag type="danger">点赞: {{ stats.like_count || 0 }}</el-tag>
        <el-tag type="success">关注: {{ stats.follow_count || 0 }}</el-tag>
        <el-tag>进入: {{ stats.member_count || 0 }}</el-tag>
      </div>
    </el-card>

    <!-- 实时消息 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>实时消息</span>
          <el-radio-group v-model="filterType" size="small">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="chat">弹幕</el-radio-button>
            <el-radio-button label="gift">礼物</el-radio-button>
            <el-radio-button label="like">点赞</el-radio-button>
            <el-radio-button label="follow">关注</el-radio-button>
            <el-radio-button label="member">进入</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div class="danmu-container" ref="danmuContainer">
        <div v-for="(item, index) in filteredList" :key="index" class="danmu-item" :class="item.msg_type">
          <span class="time">{{ item.time }}</span>
          <span class="type-tag" :class="item.msg_type">{{ getTypeLabel(item.msg_type) }}</span>
          <span class="user">{{ item.user }}:</span>
          <span class="content" v-html="item.content"></span>
        </div>
        <div v-if="!filteredList.length" class="empty">
          <el-empty description="暂无消息数据" :image-size="100" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Link, Search, View } from '@element-plus/icons-vue'
import api from '../api'

// 输入模式
const inputMode = ref('url')
const inputUrl = ref('')
const searchKeyword = ref('')

// 状态
const listening = ref(false)
const starting = ref(false)
const stopping = ref(false)
const previewing = ref(false)
const searching = ref(false)

// 数据
const previewData = ref(null)
const searchResults = ref([])
const selectedRoom = ref(null)
const danmuList = ref([])
const filterType = ref('')
const stats = ref(null)
let ws = null

// 格式化数字
const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num || 0
}

const formatTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN')
}

const getTypeLabel = (type) => {
  const labels = {
    chat: '弹幕',
    gift: '礼物',
    like: '点赞',
    follow: '关注',
    member: '进入',
    room_stats: '统计',
    system: '系统'
  }
  return labels[type] || type
}

const formatContent = (data) => {
  const type = data.msg_type
  const user = data.user?.nickname || '未知用户'

  switch (type) {
    case 'chat':
      return data.content || ''
    case 'gift':
      const gift = data.gift || {}
      const toUser = data.to_user?.nickname || '主播'
      return `送给 ${toUser} <span class="gift-name">${gift.name || '礼物'}</span> x${gift.count || 1}`
    case 'like':
      return `点赞了 ${data.like_count || 1} 次，总点赞 ${data.like_total || 0}`
    case 'follow':
      return '关注了主播'
    case 'member':
      return `进入直播间，当前观众 ${data.member_count || 0} 人`
    case 'room_stats':
      return data.display || ''
    default:
      return JSON.stringify(data)
  }
}

const filteredList = computed(() => {
  if (!filterType.value) return danmuList.value
  return danmuList.value.filter(item => item.msg_type === filterType.value)
})

const scrollToBottom = () => {
  nextTick(() => {
    const container = document.querySelector('.danmu-container')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

// 预览直播间
const previewRoom = async () => {
  if (!inputUrl.value.trim()) {
    ElMessage.warning('请输入直播间链接或房间号')
    return
  }

  previewing.value = true
  previewData.value = null
  searchResults.value = []

  try {
    const res = await api.post('/live/preview', { url: inputUrl.value.trim() })
    if (res.code === 200) {
      previewData.value = res.data
      if (!res.data.is_living) {
        ElMessage.info('该主播当前未开播')
      }
    } else {
      ElMessage.error(res.message || '获取直播间信息失败')
    }
  } catch (e) {
    ElMessage.error('获取直播间信息失败')
  } finally {
    previewing.value = false
  }
}

// 搜索直播
const searchLive = async () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  previewData.value = null
  searchResults.value = []

  try {
    const res = await api.post('/live/search', {
      keyword: searchKeyword.value.trim(),
      count: 20
    })
    if (res.code === 200) {
      searchResults.value = res.data?.items || []
      if (searchResults.value.length === 0) {
        ElMessage.info('未找到相关直播间')
      } else {
        ElMessage.success(`找到 ${searchResults.value.length} 个直播间`)
      }
    } else {
      ElMessage.error(res.message || '搜索失败')
    }
  } catch (e) {
    console.error('搜索失败:', e)
    ElMessage.error('搜索失败: ' + (e.message || '未知错误'))
  } finally {
    searching.value = false
  }
}

// 选择直播间
const selectRoom = (item) => {
  selectedRoom.value = item
  previewData.value = {
    room_id: item.room_id,
    room_title: item.room_title,
    is_living: item.is_living,
    status_text: item.is_living ? '直播中' : '未开播',
    owner: item.owner
  }
}

// 开始监听
const startListen = async () => {
  if (!previewData.value?.room_id) {
    ElMessage.warning('请先选择或输入直播间')
    return
  }

  if (!previewData.value.is_living) {
    ElMessage.warning('该主播当前未开播，无法监听')
    return
  }

  starting.value = true

  try {
    const webRid = previewData.value.web_rid || previewData.value.room_id
    const res = await api.post('/live/start-by-url', { url: webRid })
    if (res.code !== 200) {
      ElMessage.error(res.message || '启动监听失败')
      starting.value = false
      return
    }

    stats.value = res.data.stats
    const roomInfo = res.data.room_info

    const wsUrl = `ws://${location.host}/ws/live/${previewData.value.room_id}`
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      listening.value = true
      starting.value = false
      addDanmu({
        msg_type: 'system',
        user: '系统',
        content: `已连接直播间: ${roomInfo?.room_title || previewData.value.room_title || previewData.value.room_id}`,
        time: formatTime()
      })
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleMessage(data)
      } catch (e) {
        console.error('解析消息失败:', e)
      }
    }

    ws.onclose = () => {
      listening.value = false
      addDanmu({
        msg_type: 'system',
        user: '系统',
        content: '连接已断开',
        time: formatTime()
      })
    }

    ws.onerror = () => {
      listening.value = false
      starting.value = false
      ElMessage.error('WebSocket 连接失败')
    }

  } catch (e) {
    starting.value = false
    ElMessage.error('启动监听失败: ' + (e.message || '未知错误'))
  }
}

const handleMessage = (data) => {
  const type = data.msg_type
  const user = data.user?.nickname || '未知用户'

  // 更新统计
  if (stats.value) {
    if (type === 'chat') stats.value.danmu_count++
    if (type === 'gift') stats.value.gift_count++
    if (type === 'like') stats.value.like_count += (data.like_count || 1)
    if (type === 'follow') stats.value.follow_count++
    if (type === 'member') stats.value.member_count = data.member_count
  }

  addDanmu({
    msg_type: type,
    user: user,
    content: formatContent(data),
    time: formatTime(),
    rawData: data
  })
}

const stopListen = async () => {
  stopping.value = true

  try {
    // 关闭 WebSocket
    if (ws) {
      ws.close()
      ws = null
    }

    // 调用后端 API 停止监听
    if (previewData.value?.room_id) {
      await api.post(`/live/rooms/${previewData.value.room_id}/stop`)
    }

    listening.value = false
    stopping.value = false

    addDanmu({
      msg_type: 'system',
      user: '系统',
      content: '已停止监听',
      time: formatTime()
    })

    // 显示最终统计
    if (stats.value) {
      ElMessage.success(`本次监听统计 - 弹幕:${stats.value.danmu_count} 礼物:${stats.value.gift_count} 点赞:${stats.value.like_count}`)
    }

  } catch (e) {
    stopping.value = false
    ElMessage.error('停止监听失败')
  }
}

const addDanmu = (item) => {
  danmuList.value.push(item)
  if (danmuList.value.length > 500) {
    danmuList.value.shift()
  }
  scrollToBottom()
}

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-tabs {
  margin-bottom: 20px;
}

/* 预览区域 */
.preview-box {
  margin-top: 20px;
  padding: 20px;
  background: var(--accent-gradient);
  border-radius: var(--radius-lg);
  color: white;
}

.preview-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-info h3 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.preview-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-meta .room-id {
  opacity: 0.9;
  font-size: 14px;
}

.preview-actions {
  display: flex;
  gap: 10px;
}

/* 搜索结果 */
.search-results {
  margin-top: 20px;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  color: #666;
}

.live-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.live-card {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
}

.live-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.live-card.active {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px rgba(254, 44, 85, 0.2);
}

.live-cover {
  position: relative;
  height: 135px;
  background: var(--bg-tertiary);
}

.live-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.live-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #999;
  color: white;
}

.live-badge.living {
  background: var(--accent-primary);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.viewer-count {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  display: flex;
  align-items: center;
  gap: 4px;
}

.live-info {
  padding: 12px;
}

.live-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.live-owner {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.live-owner .avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

.live-owner .followers {
  color: #999;
  margin-left: auto;
}

/* 统计信息 */
.stats-row {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 消息区域 */
.danmu-container {
  height: 500px;
  overflow-y: auto;
  background: var(--bg-tertiary);
  padding: 10px;
  border-radius: var(--radius-sm);
}

.danmu-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.danmu-item.gift {
  background: linear-gradient(90deg, rgba(254, 44, 85, 0.15) 0%, transparent 100%);
  padding: 8px;
  margin: 2px 0;
  border-radius: var(--radius-sm);
}

.danmu-item.follow {
  background: linear-gradient(90deg, rgba(37, 244, 238, 0.15) 0%, transparent 100%);
  padding: 8px;
  margin: 2px 0;
  border-radius: var(--radius-sm);
}

.danmu-item .time {
  color: #999;
  font-size: 12px;
  white-space: nowrap;
}

.danmu-item .type-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.type-tag.chat { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.type-tag.gift { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.type-tag.like { background: rgba(254, 44, 85, 0.15); color: #ff6b8a; }
.type-tag.follow { background: rgba(37, 244, 238, 0.15); color: #00d4aa; }
.type-tag.member { background: rgba(160, 160, 176, 0.15); color: var(--text-secondary); }
.type-tag.system { background: rgba(160, 160, 176, 0.15); color: var(--text-primary); }

.danmu-item .user {
  color: var(--accent-secondary);
  font-weight: bold;
  white-space: nowrap;
}

.danmu-item .content {
  color: #333;
  flex: 1;
}

.gift-name {
  color: var(--accent-primary);
  font-weight: bold;
}

.empty {
  text-align: center;
  color: #999;
  padding: 40px;
}
</style>
