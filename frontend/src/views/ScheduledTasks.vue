<template>
  <div class="scheduled-tasks-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">定时任务</h1>
        <p class="page-desc">管理和配置自动化采集任务</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" size="large" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建任务
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
        <div class="stat-icon active">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.active }}</span>
          <span class="stat-label">运行中</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon paused">
          <el-icon><VideoPause /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.paused }}</span>
          <span class="stat-label">已暂停</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon runs">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.todayRuns }}</span>
          <span class="stat-label">今日执行</span>
        </div>
      </div>
    </div>

    <div class="table-section">
      <div class="table-header">
        <h3>任务列表</h3>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" class="modern-table">
        <el-table-column prop="name" label="任务名称" min-width="150">
          <template #default="{ row }">
            <div class="task-name">
              <el-icon class="task-icon" :class="row.task_type">
                <component :is="getTaskIcon(row.task_type)" />
              </el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="task_type" label="任务类型" width="120">
          <template #default="{ row }">
            <div class="task-type-badge" :class="row.task_type">
              {{ getTaskTypeName(row.task_type) }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="cron_expression" label="执行周期" width="160">
          <template #default="{ row }">
            <div class="cron-cell">
              <el-icon><Timer /></el-icon>
              <code>{{ row.cron_expression }}</code>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <div class="status-switch" :class="{ active: row.is_active }">
              <span class="status-dot"></span>
              <span>{{ row.is_active ? '运行中' : '已暂停' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次执行" min-width="180">
          <template #default="{ row }">
            <div class="time-cell" v-if="row.last_run_at">
              <el-icon><Clock /></el-icon>
              <span>{{ formatTime(row.last_run_at) }}</span>
            </div>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="next_run_at" label="下次执行" min-width="180">
          <template #default="{ row }">
            <div class="time-cell next" v-if="row.next_run_at && row.is_active">
              <el-icon><AlarmClock /></el-icon>
              <span>{{ formatTime(row.next_run_at) }}</span>
            </div>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="180">
          <template #default="{ row }">
            <div class="time-cell">
              <el-icon><Calendar /></el-icon>
              <span>{{ formatTime(row.created_at) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="success" size="small" @click="handleRunNow(row)">
                <el-icon><VideoPlay /></el-icon>
                执行
              </el-button>
              <el-button 
                :type="row.is_active ? 'warning' : 'primary'" 
                size="small" 
                @click="handleToggle(row)"
              >
                <el-icon>
                  <component :is="row.is_active ? 'VideoPause' : 'VideoPlay'" />
                </el-icon>
                {{ row.is_active ? '暂停' : '启用' }}
              </el-button>
              <el-button type="primary" size="small" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
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

    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑定时任务' : '新建定时任务'" 
      width="650px"
      class="modern-dialog"
    >
      <div class="dialog-content">
        <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
          <el-form-item label="任务名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入任务名称" size="large">
              <template #prefix>
                <el-icon><Document /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="任务类型" prop="task_type">
            <el-select v-model="form.task_type" placeholder="请选择任务类型" size="large" style="width: 100%">
              <el-option label="采集用户作品" value="user_works">
                <div class="option-content">
                  <el-icon><User /></el-icon>
                  <span>采集用户作品</span>
                </div>
              </el-option>
              <el-option label="搜索作品" value="search_works">
                <div class="option-content">
                  <el-icon><VideoPlay /></el-icon>
                  <span>搜索作品</span>
                </div>
              </el-option>
              <el-option label="搜索用户" value="search_users">
                <div class="option-content">
                  <el-icon><Search /></el-icon>
                  <span>搜索用户</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="任务参数" prop="task_params">
            <el-input 
              v-model="form.task_params" 
              type="textarea" 
              :rows="5" 
              placeholder="请输入JSON格式的任务参数"
              class="code-input"
            />
            <div class="param-hint">
              <el-icon><InfoFilled /></el-icon>
              <span>参数示例：{"keyword": "关键词", "max_count": 50}</span>
            </div>
          </el-form-item>

          <el-form-item label="Cron表达式" prop="cron_expression">
            <el-input v-model="form.cron_expression" placeholder="例如: 0 0 2 * * ?" size="large">
              <template #prefix>
                <el-icon><Timer /></el-icon>
              </template>
            </el-input>
            <div class="cron-presets">
              <div class="preset-label">常用表达式：</div>
              <div class="preset-items">
                <div class="preset-item" @click="form.cron_expression = '0 0 2 * * ?'">
                  <code>0 0 2 * * ?</code>
                  <span>每天凌晨2点</span>
                </div>
                <div class="preset-item" @click="form.cron_expression = '0 0 */6 * * ?'">
                  <code>0 0 */6 * * ?</code>
                  <span>每6小时</span>
                </div>
                <div class="preset-item" @click="form.cron_expression = '0 30 9 * * ?'">
                  <code>0 30 9 * * ?</code>
                  <span>每天9:30</span>
                </div>
                <div class="preset-item" @click="form.cron_expression = '0 0 0 * * MON'">
                  <code>0 0 0 * * MON</code>
                  <span>每周一凌晨</span>
                </div>
              </div>
            </div>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button size="large" @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" size="large" @click="submitForm" :loading="submitLoading">
            <el-icon><Check /></el-icon>
            {{ isEdit ? '保存修改' : '创建任务' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { scheduledTasksApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 20
})

const stats = computed(() => {
  const totalTasks = tableData.value.length
  const activeTasks = tableData.value.filter(t => t.is_active).length
  const pausedTasks = totalTasks - activeTasks
  return {
    total: total.value,
    active: activeTasks,
    paused: pausedTasks,
    todayRuns: 0
  }
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const editId = ref(null)

const form = reactive({
  name: '',
  task_type: '',
  task_params: '',
  cron_expression: ''
})

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  task_params: [{ required: true, message: '请输入任务参数', trigger: 'blur' }],
  cron_expression: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await scheduledTasksApi.list(queryParams)
    tableData.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  form.name = ''
  form.task_type = ''
  form.task_params = ''
  form.cron_expression = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.name = row.name
  form.task_type = row.task_type
  form.task_params = row.task_params
  form.cron_expression = row.cron_expression
  dialogVisible.value = true
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await scheduledTasksApi.update(editId.value, {
        name: form.name,
        task_params: form.task_params,
        cron_expression: form.cron_expression
      })
      ElMessage.success('更新成功')
    } else {
      await scheduledTasksApi.create(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleToggle = async (row) => {
  try {
    await scheduledTasksApi.toggle(row.id)
    ElMessage.success('状态已更新')
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleRunNow = async (row) => {
  try {
    await ElMessageBox.confirm('确定要立即执行此任务吗？', '确认', { type: 'info' })
    await scheduledTasksApi.runNow(row.id)
    ElMessage.success('任务已开始执行')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('执行失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
    await scheduledTasksApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const getTaskTypeName = (type) => {
  const map = {
    user_works: '采集作品',
    search_works: '搜索作品',
    search_users: '搜索用户'
  }
  return map[type] || type
}

const getTaskIcon = (type) => {
  const map = {
    user_works: 'User',
    search_works: 'VideoPlay',
    search_users: 'Search'
  }
  return map[type] || 'Document'
}

const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.scheduled-tasks-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  transition: var(--transition-normal);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.total {
  background: rgba(254, 44, 85, 0.1);
  color: var(--accent-primary);
}

.stat-icon.active {
  background: rgba(37, 244, 238, 0.15);
  color: var(--accent-secondary);
}

.stat-icon.paused {
  background: rgba(160, 160, 176, 0.1);
  color: var(--text-secondary);
}

.stat-icon.runs {
  background: rgba(37, 244, 238, 0.1);
  color: var(--accent-secondary);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.table-section {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.table-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modern-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--bg-tertiary);
  --el-table-row-hover-bg-color: var(--bg-card-hover);
  --el-table-border-color: var(--border-color);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-secondary);
}

.task-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.task-icon.user_works {
  background: rgba(254, 44, 85, 0.1);
  color: var(--accent-primary);
}

.task-icon.search_works {
  background: rgba(37, 244, 238, 0.15);
  color: var(--accent-secondary);
}

.task-icon.search_users {
  background: rgba(37, 244, 238, 0.1);
  color: var(--accent-secondary);
}

.task-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.task-type-badge.user_works {
  background: rgba(254, 44, 85, 0.1);
  color: var(--accent-primary);
}

.task-type-badge.search_works {
  background: rgba(37, 244, 238, 0.15);
  color: var(--accent-secondary);
}

.task-type-badge.search_users {
  background: rgba(37, 244, 238, 0.1);
  color: var(--accent-secondary);
}

.cron-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cron-cell .el-icon {
  color: var(--accent-secondary);
}

.cron-cell code {
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-primary);
}

.status-switch {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  background: rgba(160, 160, 176, 0.1);
  color: var(--text-secondary);
  font-size: 12px;
  width: fit-content;
}

.status-switch.active {
  background: rgba(37, 244, 238, 0.15);
  color: var(--accent-secondary);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
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

.time-cell.next {
  color: var(--accent-secondary);
}

.time-cell.next .el-icon {
  color: var(--accent-secondary);
}

.no-data {
  color: var(--text-muted);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
}

.modern-dialog .dialog-content {
  padding: 0;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code-input :deep(textarea) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  background: var(--bg-tertiary);
  border-color: var(--border-color);
}

.param-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.param-hint .el-icon {
  color: var(--accent-secondary);
}

.cron-presets {
  margin-top: 12px;
}

.preset-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.preset-items {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.preset-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition-fast);
}

.preset-item:hover {
  background: var(--bg-card-hover);
}

.preset-item code {
  background: var(--bg-card);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--accent-secondary);
}

.preset-item span {
  font-size: 12px;
  color: var(--text-secondary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-wrap: wrap;
  }
  
  .preset-items {
    grid-template-columns: 1fr;
  }
}
</style>
