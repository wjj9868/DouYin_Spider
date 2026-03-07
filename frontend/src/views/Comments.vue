<template>
  <div class="comments-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">作品评论</h1>
        <p class="page-desc">查看和管理作品评论数据</p>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
      </div>
    </div>

    <div class="stats-cards" v-if="selectedWork">
      <div class="stat-card">
        <div class="stat-icon comments">
          <el-icon><ChatDotRound /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total }}</span>
          <span class="stat-label">评论总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon likes">
          <el-icon><Star /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(stats.totalLikes) }}</span>
          <span class="stat-label">总点赞</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon replies">
          <el-icon><ChatLineRound /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalReplies }}</span>
          <span class="stat-label">总回复</span>
        </div>
      </div>
    </div>

    <div class="work-selector-section">
      <div class="selector-label">选择作品</div>
      <el-select
        v-model="selectedWork"
        placeholder="选择要查看评论的作品"
        filterable
        @change="handleWorkChange"
        class="work-select"
      >
        <el-option
          v-for="work in workList"
          :key="work.work_id"
          :label="work.title || '无标题作品'"
          :value="work.work_id"
        >
          <div class="work-option">
            <el-image :src="work.cover_url" class="option-cover" fit="cover">
              <template #error>
                <div class="cover-placeholder">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div class="option-info">
              <span class="option-title">{{ work.title || '无标题作品' }}</span>
              <span class="option-stats">
                <el-icon><Star /></el-icon> {{ formatNumber(work.digg_count) }}
                <el-icon style="margin-left: 8px"><ChatDotRound /></el-icon> {{ formatNumber(work.comment_count) }}
              </span>
            </div>
          </div>
        </el-option>
      </el-select>
    </div>

    <div class="comments-section" v-if="selectedWork">
      <div class="section-header">
        <div class="section-title">
          <el-icon><ChatDotRound /></el-icon>
          <span>评论列表</span>
          <span class="comment-count" v-if="total">{{ total }} 条</span>
        </div>
        <div class="section-actions">
          <el-button type="primary" @click="handleCollect" :loading="collecting">
            <el-icon><Download /></el-icon>
            采集评论
          </el-button>
          <el-button @click="loadComments" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <div class="comments-list" v-loading="loading">
        <el-table :data="commentList" class="modern-table" v-if="commentList.length > 0">
          <el-table-column label="用户" width="200">
            <template #default="{ row }">
              <div class="user-cell">
                <el-avatar :src="row.user_avatar" :size="40" class="user-avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <div class="user-info">
                  <div class="user-name">{{ row.user_nickname || '匿名用户' }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="content" label="评论内容" min-width="300">
            <template #default="{ row }">
              <div class="comment-text">{{ row.content }}</div>
            </template>
          </el-table-column>
          <el-table-column label="互动" width="120">
            <template #default="{ row }">
              <div class="interaction-stats">
                <div class="stat-row">
                  <el-icon class="stat-icon like"><Star /></el-icon>
                  <span>{{ formatNumber(row.digg_count) }}</span>
                </div>
                <div class="stat-row" v-if="row.reply_count">
                  <el-icon class="stat-icon reply"><ChatLineRound /></el-icon>
                  <span>{{ row.reply_count }} 回复</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="create_time" label="时间" width="160">
            <template #default="{ row }">
              <div class="time-cell">
                <el-icon><Clock /></el-icon>
                <span>{{ formatTime(row.create_time) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.reply_count > 0"
                type="primary"
                size="small"
                circle
                @click="showReplies(row)"
              >
                <el-icon><ChatLineRound /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="empty-state" v-else-if="!loading">
          <el-icon class="empty-icon"><ChatDotRound /></el-icon>
          <p>暂无评论数据</p>
          <el-button type="primary" @click="handleCollect">立即采集</el-button>
        </div>
      </div>

      <div class="pagination-wrapper" v-if="commentList.length > 0">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadComments"
        />
      </div>
    </div>

    <div class="empty-selector" v-else>
      <el-icon class="empty-icon"><ChatDotRound /></el-icon>
      <p>请先选择一个作品</p>
    </div>

    <el-drawer v-model="repliesDrawerVisible" title="评论回复" size="500px" class="detail-drawer">
      <div v-if="currentComment" class="replies-content">
        <div class="original-comment">
          <div class="comment-header">
            <el-avatar :src="currentComment.user_avatar" :size="36" />
            <div class="comment-meta">
              <span class="author">{{ currentComment.user_nickname || '匿名用户' }}</span>
              <span class="time">{{ formatTime(currentComment.create_time) }}</span>
            </div>
          </div>
          <div class="comment-body">{{ currentComment.content }}</div>
        </div>

        <div class="replies-header">
          <span>回复 ({{ currentComment.reply_count || 0 }})</span>
        </div>

        <div class="replies-list" v-loading="repliesLoading">
          <div class="reply-item" v-for="reply in repliesList" :key="reply.id">
            <el-avatar :src="reply.user_avatar" :size="32" />
            <div class="reply-content">
              <div class="reply-header">
                <span class="reply-author">{{ reply.user_nickname || '匿名用户' }}</span>
                <span class="reply-time">{{ formatTime(reply.create_time) }}</span>
              </div>
              <div class="reply-text">{{ reply.content }}</div>
            </div>
          </div>
          <div class="empty-replies" v-if="!repliesLoading && repliesList.length === 0">
            暂无回复
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { worksApi, commentsApi, exportApi } from '@/api'

const selectedWork = ref('')
const workList = ref([])
const commentList = ref([])
const total = ref(0)
const loading = ref(false)
const collecting = ref(false)

const currentPage = ref(1)
const pageSize = ref(20)

const repliesDrawerVisible = ref(false)
const currentComment = ref(null)
const repliesList = ref([])
const repliesLoading = ref(false)

const stats = reactive({
  total: 0,
  totalLikes: 0,
  totalReplies: 0
})

const loadWorkList = async () => {
  try {
    const res = await worksApi.list({ page_size: 100 })
    if (res.code === 0) {
      workList.value = res.data.items
    }
  } catch (error) {
    console.error('加载作品列表失败', error)
  }
}

const handleWorkChange = () => {
  currentPage.value = 1
  commentList.value = []
  loadComments()
}

const loadComments = async () => {
  if (!selectedWork.value) return

  loading.value = true
  try {
    const res = await commentsApi.list(selectedWork.value, {
      page: currentPage.value,
      page_size: pageSize.value
    })

    if (res.code === 0) {
      commentList.value = res.data.items
      total.value = res.data.total

      // 更新统计
      stats.total = res.data.total
      stats.totalLikes = commentList.value.reduce((sum, c) => sum + (c.digg_count || 0), 0)
      stats.totalReplies = commentList.value.reduce((sum, c) => sum + (c.reply_count || 0), 0)
    } else {
      ElMessage.error(res.message || '获取评论失败')
    }
  } catch (error) {
    ElMessage.error('获取评论失败')
  } finally {
    loading.value = false
  }
}

const handleCollect = async () => {
  if (!selectedWork.value) return

  collecting.value = true
  try {
    const res = await commentsApi.collect(selectedWork.value, 200)
    if (res.code === 0) {
      ElMessage.success('评论采集任务已创建')
    } else {
      ElMessage.error(res.message || '采集失败')
    }
  } catch (error) {
    ElMessage.error('采集失败')
  } finally {
    collecting.value = false
  }
}

const showReplies = async (comment) => {
  currentComment.value = comment
  repliesDrawerVisible.value = true
  repliesList.value = []
  repliesLoading.value = true

  try {
    const res = await commentsApi.getReplies(selectedWork.value, comment.comment_id, {
      page: 1,
      page_size: 50
    })

    if (res.code === 0) {
      repliesList.value = res.data.items
    }
  } catch (error) {
    ElMessage.error('获取回复失败')
  } finally {
    repliesLoading.value = false
  }
}

const handleExport = async () => {
  if (!selectedWork.value) {
    ElMessage.warning('请先选择作品')
    return
  }
  try {
    const res = await exportApi.comments({ work_id: selectedWork.value })
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `comments_${selectedWork.value}_${Date.now()}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 2592000000) return Math.floor(diff / 86400000) + '天前'

  return date.toLocaleDateString()
}

onMounted(() => {
  loadWorkList()
})
</script>

<style scoped>
.comments-page {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.page-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--transition-normal);
}

.stat-card:hover {
  border-color: var(--border-hover);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.comments { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.stat-icon.likes { background: rgba(255, 193, 7, 0.15); color: #ffc107; }
.stat-icon.replies { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }

.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-muted); }

.work-selector-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 20px;
}

.selector-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.work-select {
  width: 100%;
  max-width: 500px;
}

.work-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.option-cover {
  width: 48px;
  height: 64px;
  border-radius: 6px;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.option-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-title {
  font-size: 14px;
  color: var(--text-primary);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.option-stats {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
}

.comments-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.comment-count {
  background: rgba(254, 44, 85, 0.15);
  color: var(--accent-primary);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.comments-list {
  min-height: 200px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  flex-shrink: 0;
  background: var(--bg-tertiary);
}

.user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.comment-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  word-break: break-word;
}

.interaction-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.stat-row .stat-icon.like { color: var(--accent-primary); }
.stat-row .stat-icon.reply { color: var(--accent-secondary); }

.time-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.pagination-wrapper {
  padding: 20px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--border-color);
}

.empty-state,
.empty-selector {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.detail-drawer .replies-content {
  padding: 0 20px;
}

.original-comment {
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: 20px;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.comment-meta {
  display: flex;
  flex-direction: column;
}

.comment-meta .author {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.comment-meta .time {
  font-size: 12px;
  color: var(--text-muted);
}

.comment-body {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.replies-header {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.replies-list {
  min-height: 100px;
}

.reply-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}

.reply-content {
  flex: 1;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.reply-author {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.reply-time {
  font-size: 11px;
  color: var(--text-muted);
}

.reply-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.empty-replies {
  text-align: center;
  color: var(--text-muted);
  padding: 40px 0;
}
</style>
