<template>
  <div class="tasks-page">
    <el-card>
      <template #header>
        <span>任务管理</span>
      </template>

      <el-form inline>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="等待" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="task_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.task_type)" size="small">
              {{ getTypeName(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="150">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :status="getStatus(row.status)" />
          </template>
        </el-table-column>
        <el-table-column prop="result_count" label="已采集" width="80" />
        <el-table-column prop="task_params" label="参数" min-width="150">
          <template #default="{ row }">
            {{ JSON.stringify(row.task_params) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleDelete(row.id)" :disabled="row.status === 'running'">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tasksApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  status: ''
})

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

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗?', '提示', { type: 'warning' })
    await tasksApi.delete(id)
    ElMessage.success('删除成功')
    loadData()
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

const getTypeColor = (type) => {
  const map = { work: 'primary', user_works: 'success', search: 'warning', comment: 'info' }
  return map[type] || ''
}

const getStatusName = (status) => {
  const map = { pending: '等待', running: '运行中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

const getStatusColor = (status) => {
  const map = { pending: 'info', running: '', completed: 'success', failed: 'danger' }
  return map[status] || ''
}

const getStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadData()
  // 定时刷新
  setInterval(loadData, 5000)
})
</script>
