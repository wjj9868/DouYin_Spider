<template>
  <div class="tasks-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">任务管理</h1>
        <p class="page-desc">查看和管理采集任务执行状态</p>
      </div>
      <div class="header-actions">
        <el-button v-if="selectedTasks.length" type="danger" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除 ({{ selectedTasks.length }})
        </el-button>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon total">
          <el-icon><List /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total }}</span>
          <span class="stat-label">总任务数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon pending">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.pending }}</span>
          <span class="stat-label">等待中</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon running">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.running }}</span>
          <span class="stat-label">运行中</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon completed">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.completed }}</span>
          <span class="stat-label">已完成</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon failed">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.failed }}</span>
          <span class="stat-label">失败</span>
        </div>
      </div>
    </div>

    <div class="quick-filters">
      <div class="filter-tags">
        <span class="filter-label">快捷筛选：</span>
        <el-tag 
          v-for="tag in quickFilters" 
          :key="tag.value"
          :type="activeQuickFilter === tag.value ? '' : 'info'"
          :effect="activeQuickFilter === tag.value ? 'dark' : 'plain'"
          @click="applyQuickFilter(tag.value)"
          class="filter-tag"
        >
          {{ tag.label }}
        </el-tag>
      </div>
    </div>

    <div class="table-section">
      <el-table :data="tableData" v-loading="loading" @selection-change="handleSelectionChange" class="modern-table">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="70">
          <template #default="{ row }">
            <span class="task-id" @click="showDetail(row)">#{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="task_type" label="任务类型" width="130">
          <template #default="{ row }">
            <div class="task-type-badge" :class="row.task_type">
              <el-icon>
                <component :is="getTypeIcon(row.task_type)" />
              </el-icon>
              <span>{{ getTypeName(row.task_type) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <div class="status-badge" :class="row.status">
              <span class="status-dot"></span>
              <span>{{ getStatusName(row.status) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" min-width="180">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress 
                :percentage="row.progress || 0" 
                :stroke-width="8"
                :status="getProgressStatus(row.status)"
              />
              <span class="progress-text">{{ row.result_count || 0 }} 条数据</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="task_params" label="任务参数" min-width="160">
          <template #default="{ row }">
            <div class="params-cell">
              <el-icon><Document /></el-icon>
              <code>{{ formatParams(row.task_params) }}</code>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160">
          <template #default="{ row }">
            <div class="time-cell">
              <el-icon><Clock /></el-icon>
              <span>{{ formatTime(row.created_at) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-tooltip content="查看详情" placement="top">
                <el-button type="primary" size="small" circle @click="showDetail(row)">
                  <el-icon><View /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip v-if="row.status === 'failed'" content="重试任务" placement="top">
                <el-button type="warning" size="small" circle @click="handleRetry(row)">
                  <el-icon><RefreshRight /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip v-if="row.status === 'running' || row.status === 'pending'" content="取消任务" placement="top">
                <el-button type="info" size="small" circle @click="handleCancel(row)">
                  <el-icon><Close /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button type="danger" size="small" circle @click="handleDelete(row.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>

    <el-drawer v-model="detailDrawerVisible" :title="`任务详情 #${currentTask?.id || ''}`" size="550px" class="detail-drawer">
      <div v-if="currentTask" class="detail-content">
        <div class="task-header" :class="currentTask.status">
          <div class="task-icon">
            <el-icon>
              <component :is="getTypeIcon(currentTask.task_type)" />
            </el-icon>
          </div>
          <div class="task-info">
            <div class="task-type">{{ getTypeName(currentTask.task_type) }}</div>
            <div class="task-status">
              <span class="status-badge" :class="currentTask.status">
                <span class="status-dot"></span>
                <span>{{ getStatusName(currentTask.status) }}</span>
              </span>
            </div>
          </div>
        </div>

        <div class="progress-section">
          <div class="progress-header">
            <span class="progress-label">执行进度</span>
            <span class="progress-value">{{ currentTask.progress || 0 }}%</span>
          </div>
          <el-progress 
            :percentage="currentTask.progress || 0" 
            :stroke-width="12"
            :status="getProgressStatus(currentTask.status)"
          />
          <div class="progress-stats">
            <div class="stat">
              <el-icon><DataLine /></el-icon>
              <span>已采集 {{ currentTask.result_count || 0 }} 条数据</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>任务参数</h4>
          <div class="params-display">
            <pre>{{ JSON.stringify(currentTask.task_params, null, 2) }}</pre>
          </div>
        </div>

        <div class="detail-section">
          <h4>时间信息</h4>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">创建时间</span>
              <span class="info-value">{{ formatTime(currentTask.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">开始时间</span>
              <span class="info-value">{{ currentTask.started_at ? formatTime(currentTask.started_at) : '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">完成时间</span>
              <span class="info-value">{{ currentTask.finished_at ? formatTime(currentTask.finished_at) : '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">耗时</span>
              <span class="info-value">{{ getDuration(currentTask) }}</span>
            </div>
          </div>
        </div>

        <div v-if="currentTask.error_message" class="detail-section error-section">
          <h4>错误信息</h4>
          <div class="error-message">
            <el-icon><Warning /></el-icon>
            <span>{{ currentTask.error_message }}</span>
          </div>
        </div>

        <div class="detail-actions">
          <el-button v-if="currentTask.status === 'failed'" type="warning" @click="handleRetry(currentTask)">
            <el-icon><RefreshRight /></el-icon>
            重试任务
          </el-button>
          <el-button v-if="currentTask.status === 'running' || currentTask.status === 'pending'" type="info" @click="handleCancel(currentTask)">
            <el-icon><Close /></el-icon>
            取消任务
          </el-button>
          <el-button type="danger" @click="handleDelete(currentTask.id)">
            <el-icon><Delete /></el-icon>
            删除任务
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tasksApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedTasks = ref([])
const detailDrawerVisible = ref(false)
const currentTask = ref(null)
const activeQuickFilter = ref('')

const queryParams = reactive({
  page: 1,
  page_size: 20,
  status: ''
})

const stats = ref({
  total: 0,
  pending: 0,
  running: 0,
  completed: 0,
  failed: 0
})

const quickFilters = [
  { label: '全部', value: '' },
  { label: '等待中', value: 'pending' },
  { label: '运行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
]

let refreshTimer = null

const loadStats = async () => {
  try {
    const res = await tasksApi.stats()
    stats.value = {
      total: res.data.total,
      pending: res.data.pending,
      running: res.data.running,
      completed: res.data.completed,
      failed: res.data.failed
    }
  } catch (e) {
    console.error('加载统计失败')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await tasksApi.list(queryParams)
    tableData.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const applyQuickFilter = (filter) => {
  activeQuickFilter.value = filter
  queryParams.status = filter
  queryParams.page = 1
  loadData()
}

const handleSelectionChange = (selection) => {
  selectedTasks.value = selection
}

const showDetail = (row) => {
  currentTask.value = row
  detailDrawerVisible.value = true
}

const handleRetry = async (row) => {
  try {
    await ElMessageBox.confirm('确定要重试该任务吗？', '确认重试', { type: 'info' })
    await tasksApi.retry(row.id)
    ElMessage.success('任务已重新开始执行')
    detailDrawerVisible.value = false
    loadData()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.message || '重试失败')
    }
  }
}

const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm('确定要取消该任务吗？', '确认取消', { type: 'warning' })
    await tasksApi.cancel(row.id)
    ElMessage.success('任务已取消')
    detailDrawerVisible.value = false
    loadData()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.message || '取消失败')
    }
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗?', '提示', { type: 'warning' })
    await tasksApi.delete(id)
    ElMessage.success('删除成功')
    detailDrawerVisible.value = false
    loadData()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedTasks.value.length} 个任务吗？`, '确认删除', { type: 'warning' })
    const ids = selectedTasks.value.map(t => t.id)
    await tasksApi.batchDelete(ids)
    ElMessage.success('批量删除成功')
    loadData()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getTypeName = (type) => {
  const map = { work: '作品', user_works: '用户作品', search: '搜索', comment: '评论' }
  return map[type] || type
}

const getTypeIcon = (type) => {
  const map = { 
    work: 'VideoPlay', 
    user_works: 'User', 
    search: 'Search', 
    comment: 'ChatDotRound' 
  }
  return map[type] || 'Document'
}

const getStatusName = (status) => {
  const map = { pending: '等待中', running: '运行中', completed: '已完成', failed: '失败', cancelled: '已取消' }
  return map[status] || status
}

const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}

const getDuration = (task) => {
  if (!task.started_at) return '-'
  const start = new Date(task.started_at)
  const end = task.finished_at ? new Date(task.finished_at) : new Date()
  const diff = Math.floor((end - start) / 1000)
  if (diff < 60) return `${diff}秒`
  if (diff < 3600) return `${Math.floor(diff / 60)}分${diff % 60}秒`
  return `${Math.floor(diff / 3600)}时${Math.floor((diff % 3600) / 60)}分`
}

const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatParams = (params) => {
  if (!params) return '-'
  try {
    const str = JSON.stringify(params)
    return str.length > 30 ? str.substring(0, 30) + '...' : str
  } catch {
    return '-'
  }
}

onMounted(() => {
  loadData()
  loadStats()
  refreshTimer = setInterval(() => {
    loadData()
    loadStats()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.tasks-page {
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

.header-left {
  flex: 1;
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

.stats-cards .stat-card {
  flex: 1;
  min-width: 0;
}

.stat-card {
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

.stat-icon.total { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.stat-icon.pending { background: rgba(160, 160, 176, 0.15); color: var(--text-secondary); }
.stat-icon.running { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.stat-icon.completed { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.stat-icon.failed { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }

.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-muted); }

.quick-filters {
  margin-bottom: 16px;
}

.filter-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.filter-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tag:hover {
  transform: scale(1.05);
}

.table-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.task-id {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: var(--accent-primary);
  cursor: pointer;
}

.task-id:hover {
  text-decoration: underline;
}

.task-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.task-type-badge.work { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.task-type-badge.user_works { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.task-type-badge.search { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.task-type-badge.comment { background: rgba(254, 44, 85, 0.15); color: #ff6b8a; }

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.status-badge .status-dot {
  width: 6px;
  height: 6px;
}

.status-badge.pending { background: rgba(160, 160, 176, 0.15); color: var(--text-secondary); }
.status-badge.pending .status-dot { background: var(--text-muted); }

.status-badge.running { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.status-badge.running .status-dot { background: var(--accent-secondary); animation: pulse 1.5s ease-in-out infinite; }

.status-badge.completed { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.status-badge.completed .status-dot { background: var(--accent-secondary); }

.status-badge.failed { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.status-badge.failed .status-dot { background: var(--accent-primary); }

.status-badge.cancelled { background: rgba(160, 160, 176, 0.15); color: var(--text-muted); }
.status-badge.cancelled .status-dot { background: var(--text-muted); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-text {
  font-size: 11px;
  color: var(--text-muted);
}

.params-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.params-cell .el-icon {
  color: var(--accent-secondary);
  flex-shrink: 0;
}

.params-cell code {
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.time-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.time-cell .el-icon {
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.pagination-wrapper {
  padding: 20px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--border-color);
}

.detail-drawer .detail-content {
  padding: 0 20px;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
}

.task-header.pending { background: linear-gradient(135deg, rgba(160, 160, 176, 0.1) 0%, var(--bg-card) 100%); }
.task-header.running { background: linear-gradient(135deg, rgba(37, 244, 238, 0.1) 0%, var(--bg-card) 100%); }
.task-header.completed { background: linear-gradient(135deg, rgba(0, 212, 170, 0.1) 0%, var(--bg-card) 100%); }
.task-header.failed { background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, var(--bg-card) 100%); }

.task-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  background: var(--bg-card);
  border: 2px solid var(--border-color);
}

.task-header.pending .task-icon { color: var(--text-secondary); }
.task-header.running .task-icon { color: var(--accent-secondary); }
.task-header.completed .task-icon { color: var(--accent-secondary); }
.task-header.failed .task-icon { color: var(--accent-primary); }

.task-info {
  flex: 1;
}

.task-type {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.progress-section {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 24px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.progress-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-primary);
}

.progress-stats {
  margin-top: 12px;
  display: flex;
  gap: 16px;
}

.progress-stats .stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.params-display {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 16px;
  overflow-x: auto;
}

.params-display pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.info-label {
  font-size: 12px;
  color: var(--text-muted);
}

.info-value {
  font-size: 13px;
  color: var(--text-primary);
}

.error-section .error-message {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 16px;
  background: rgba(254, 44, 85, 0.1);
  border-radius: var(--radius-md);
  color: var(--accent-primary);
  font-size: 13px;
  line-height: 1.5;
}

.error-message .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}
</style>
