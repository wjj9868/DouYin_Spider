<template>
  <div class="works-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>作品管理</span>
          <div>
            <el-button type="primary" @click="handleCollect">采集作品</el-button>
            <el-button type="success" @click="handleExport">导出Excel</el-button>
          </div>
        </div>
      </template>

      <el-form inline>
        <el-form-item label="类型">
          <el-select v-model="queryParams.work_type" placeholder="全部" clearable style="width: 120px">
            <el-option label="视频" value="video" />
            <el-option label="图集" value="image" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="标题关键词" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" style="width: 100%">
        <el-table-column prop="cover_url" label="封面" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.cover_url"
              :src="row.cover_url"
              :preview-src-list="[row.cover_url]"
              fit="cover"
              style="width: 80px; height: 60px; border-radius: 4px;"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="work_id" label="作品ID" width="180">
          <template #default="{ row }">
            <el-link :href="row.work_url" target="_blank" type="primary">
              {{ row.work_id }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="author_nickname" label="作者" width="120">
          <template #default="{ row }">
            <el-link v-if="row.user_url" :href="row.user_url" target="_blank" type="primary">
              {{ row.author_nickname || '-' }}
            </el-link>
            <span v-else>{{ row.author_nickname || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="work_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.work_type === 'video' ? 'primary' : 'success'" size="small">
              {{ row.work_type === 'video' ? '视频' : '图集' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="视频链接" width="100">
          <template #default="{ row }">
            <el-link v-if="row.video_url" @click="playVideo(row)" type="success">
              播放视频
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="互动数据" width="200">
          <template #default="{ row }">
            <div style="font-size: 12px;">
              <span>👍{{ row.digg_count || 0 }}</span>
              <span style="margin-left: 8px;">💬{{ row.comment_count || 0 }}</span>
              <span style="margin-left: 8px;">⭐{{ row.collect_count || 0 }}</span>
              <span style="margin-left: 8px;">🔗{{ row.share_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="topics" label="话题" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.topics && row.topics.length">{{ row.topics.join(', ') }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="发布时间" width="120">
          <template #default="{ row }">
            {{ formatTime(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="crawled_at" label="采集时间" width="120">
          <template #default="{ row }">
            {{ formatTime(row.crawled_at) }}
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 采集对话框 -->
    <el-dialog v-model="collectDialogVisible" title="采集作品" width="400px">
      <el-form>
        <el-form-item label="作品ID">
          <el-input v-model="collectForm.work_id" placeholder="请输入作品ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="collectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCollect" :loading="collectLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 视频播放对话框 -->
    <el-dialog v-model="videoDialogVisible" :title="currentVideo?.title || '视频播放'" width="800px">
      <video
        v-if="videoDialogVisible && currentVideo"
        :src="`/api/works/${currentVideo.work_id}/video`"
        controls
        autoplay
        style="width: 100%; max-height: 500px;"
      />
      <template #footer>
        <el-button @click="videoDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { worksApi, exportApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const collectDialogVisible = ref(false)
const collectLoading = ref(false)
const videoDialogVisible = ref(false)
const currentVideo = ref(null)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  work_type: '',
  keyword: ''
})

const collectForm = reactive({
  work_id: ''
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await worksApi.list(queryParams)
    tableData.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleCollect = () => {
  collectForm.work_id = ''
  collectDialogVisible.value = true
}

const submitCollect = async () => {
  if (!collectForm.work_id) {
    ElMessage.warning('请输入作品ID')
    return
  }
  collectLoading.value = true
  try {
    await worksApi.collect(collectForm.work_id)
    ElMessage.success('采集任务已创建')
    collectDialogVisible.value = false
  } catch (e) {
    ElMessage.error('创建任务失败')
  } finally {
    collectLoading.value = false
  }
}

const handleExport = async () => {
  try {
    const res = await exportApi.works({ limit: 1000 })
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `works_${Date.now()}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

const resetQuery = () => {
  queryParams.keyword = ''
  queryParams.work_type = ''
  queryParams.page = 1
  loadData()
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const playVideo = (row) => {
  currentVideo.value = row
  videoDialogVisible.value = true
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
