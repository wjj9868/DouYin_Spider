<template>
  <div class="works-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">作品管理</h1>
        <p class="page-desc">管理和查看采集的抖音作品数据</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleCollect">
          <el-icon><Plus /></el-icon>
          采集作品
        </el-button>
        <el-button type="success" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
        <el-button v-if="selectedWorks.length" type="danger" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除 ({{ selectedWorks.length }})
        </el-button>
      </div>
    </div>

    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon video">
          <el-icon><VideoPlay /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.videos }}</span>
          <span class="stat-label">视频作品</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon image">
          <el-icon><Picture /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.images }}</span>
          <span class="stat-label">图集作品</span>
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
        <div class="stat-icon comments">
          <el-icon><ChatDotRound /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(stats.totalComments) }}</span>
          <span class="stat-label">总评论</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon collects">
          <el-icon><Collection /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(stats.totalCollects) }}</span>
          <span class="stat-label">总收藏</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon shares">
          <el-icon><Share /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(stats.totalShares) }}</span>
          <span class="stat-label">总分享</span>
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

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <label>类型</label>
          <el-select v-model="queryParams.work_type" placeholder="全部" clearable>
            <el-option label="视频" value="video" />
            <el-option label="图集" value="image" />
          </el-select>
        </div>
        <div class="filter-item">
          <label>关键词</label>
          <el-input v-model="queryParams.keyword" placeholder="搜索标题..." clearable @keyup.enter="loadData">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <label>点赞范围</label>
          <div class="range-inputs">
            <el-input-number v-model="queryParams.min_likes" :min="0" placeholder="最小" controls-position="right" />
            <span class="range-separator">-</span>
            <el-input-number v-model="queryParams.max_likes" :min="0" placeholder="最大" controls-position="right" />
          </div>
        </div>
        <div class="filter-actions">
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <el-table 
        :data="tableData" 
        v-loading="loading" 
        @selection-change="handleSelectionChange"
        class="modern-table"
        row-key="work_id"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="cover_url" label="封面" width="90">
          <template #default="{ row }">
            <div class="cover-cell" @click="showDetail(row)">
              <el-image
                v-if="row.cover_url"
                :src="row.cover_url"
                :preview-src-list="[row.cover_url]"
                fit="cover"
                class="cover-image"
                lazy
              />
              <div v-else class="cover-placeholder">
                <el-icon><Picture /></el-icon>
              </div>
              <div v-if="row.work_type === 'video'" class="play-overlay">
                <el-icon><VideoPlay /></el-icon>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="220">
          <template #default="{ row }">
            <div class="title-cell" @click="showDetail(row)">
              <span class="title-text">{{ row.title || '无标题' }}</span>
              <div class="title-meta">
                <el-tag size="small" :type="row.work_type === 'video' ? 'danger' : 'success'" effect="plain">
                  {{ row.work_type === 'video' ? '视频' : '图集' }}
                </el-tag>
                <span class="work-id">{{ row.work_id }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="author_nickname" label="作者" width="140">
          <template #default="{ row }">
            <div class="author-cell">
              <el-avatar :src="row.author_avatar" :size="32" class="author-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="author-info">
                <el-link v-if="row.user_url" :href="row.user_url" target="_blank" class="author-name">
                  {{ row.author_nickname || '-' }}
                </el-link>
                <span v-else class="author-name">{{ row.author_nickname || '-' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="互动数据" width="120">
          <template #default="{ row }">
            <div class="interaction-stats-vertical">
              <div class="stat-row">
                <el-icon class="stat-icon like"><Star /></el-icon>
                <span class="stat-num">{{ formatNumber(row.digg_count) }}</span>
              </div>
              <div class="stat-row">
                <el-icon class="stat-icon comment"><ChatDotRound /></el-icon>
                <span class="stat-num">{{ formatNumber(row.comment_count) }}</span>
              </div>
              <div class="stat-row">
                <el-icon class="stat-icon collect"><Collection /></el-icon>
                <span class="stat-num">{{ formatNumber(row.collect_count) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="发布时间" width="160">
          <template #default="{ row }">
            <div class="time-cell">
              <el-icon><Clock /></el-icon>
              <span>{{ formatDate(row.create_time) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-tooltip content="查看详情" placement="top">
                <el-button type="primary" size="small" circle @click="showDetail(row)">
                  <el-icon><View /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip v-if="row.work_type === 'video'" content="播放视频" placement="top">
                <el-button type="danger" size="small" circle @click="playVideo(row)">
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip v-else-if="row.images?.length" content="查看图集" placement="top">
                <el-button type="success" size="small" circle @click="viewImages(row)">
                  <el-icon><Picture /></el-icon>
                </el-button>
              </el-tooltip>
              <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
                <el-button size="small" circle>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="open" :icon="Link">打开原链接</el-dropdown-item>
                    <el-dropdown-item command="copy" :icon="CopyDocument">复制ID</el-dropdown-item>
                    <el-dropdown-item command="delete" :icon="Delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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

    <el-dialog v-model="collectDialogVisible" title="采集作品" width="500px" class="modern-dialog">
      <div class="collect-dialog">
        <el-radio-group v-model="collectMode" class="collect-mode">
          <el-radio-button value="single">单个作品</el-radio-button>
          <el-radio-button value="batch">批量采集</el-radio-button>
        </el-radio-group>
        
        <div v-if="collectMode === 'single'" class="single-input">
          <el-input v-model="collectForm.work_id" placeholder="请输入抖音作品ID或分享链接" size="large">
            <template #prefix>
              <el-icon><Link /></el-icon>
            </template>
          </el-input>
        </div>
        
        <div v-else class="batch-input">
          <el-input
            v-model="collectForm.batch_ids"
            type="textarea"
            :rows="5"
            placeholder="每行一个作品ID或分享链接，支持批量粘贴"
          />
          <div class="batch-tips">
            <el-icon><InfoFilled /></el-icon>
            <span>已输入 {{ batchCount }} 个作品</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="collectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCollect" :loading="collectLoading">
          {{ collectMode === 'batch' ? `批量采集 (${batchCount})` : '开始采集' }}
        </el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailDrawerVisible" :title="currentWork?.title || '作品详情'" size="600px" class="detail-drawer">
      <div v-if="currentWork" class="detail-content">
        <div class="detail-cover">
          <el-image
            v-if="currentWork.cover_url"
            :src="currentWork.cover_url"
            :preview-src-list="[currentWork.cover_url]"
            fit="cover"
            class="cover-img"
          />
          <div v-if="currentWork.work_type === 'video'" class="play-btn" @click="playVideo(currentWork)">
            <el-icon><VideoPlay /></el-icon>
          </div>
        </div>
        
        <div class="detail-stats">
          <div class="stat-box">
            <el-icon class="stat-icon likes"><Star /></el-icon>
            <div class="stat-content">
              <span class="stat-num">{{ formatNumber(currentWork.digg_count) }}</span>
              <span class="stat-label">点赞</span>
            </div>
          </div>
          <div class="stat-box">
            <el-icon class="stat-icon comments"><ChatDotRound /></el-icon>
            <div class="stat-content">
              <span class="stat-num">{{ formatNumber(currentWork.comment_count) }}</span>
              <span class="stat-label">评论</span>
            </div>
          </div>
          <div class="stat-box">
            <el-icon class="stat-icon collects"><Collection /></el-icon>
            <div class="stat-content">
              <span class="stat-num">{{ formatNumber(currentWork.collect_count) }}</span>
              <span class="stat-label">收藏</span>
            </div>
          </div>
          <div class="stat-box">
            <el-icon class="stat-icon shares"><Share /></el-icon>
            <div class="stat-content">
              <span class="stat-num">{{ formatNumber(currentWork.share_count) }}</span>
              <span class="stat-label">分享</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>作品信息</h4>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">作品ID</span>
              <span class="info-value">{{ currentWork.work_id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">类型</span>
              <el-tag :type="currentWork.work_type === 'video' ? 'danger' : 'success'" size="small">
                {{ currentWork.work_type === 'video' ? '视频' : '图集' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">发布时间</span>
              <span class="info-value">{{ formatDate(currentWork.create_time) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">采集时间</span>
              <span class="info-value">{{ formatDate(currentWork.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>作者信息</h4>
          <div class="author-detail">
            <el-avatar :src="currentWork.author_avatar" :size="48" />
            <div class="author-meta">
              <span class="author-name">{{ currentWork.author_nickname || '未知' }}</span>
              <span class="author-id">{{ currentWork.author_unique_id || '' }}</span>
            </div>
            <el-button type="primary" size="small" @click="openUserUrl(currentWork)">
              查看主页
            </el-button>
          </div>
        </div>

        <div v-if="currentWork.images?.length" class="detail-section">
          <h4>图集预览 ({{ currentWork.images.length }}张)</h4>
          <div class="images-grid">
            <el-image
              v-for="(img, idx) in currentWork.images.slice(0, 9)"
              :key="idx"
              :src="img"
              :preview-src-list="currentWork.images"
              :initial-index="idx"
              fit="cover"
              class="preview-img"
            />
            <div v-if="currentWork.images.length > 9" class="more-images" @click="viewImages(currentWork)">
              +{{ currentWork.images.length - 9 }}
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="openWorkUrl(currentWork)">
            <el-icon><Link /></el-icon>
            打开原作品
          </el-button>
          <el-button @click="copyWorkId(currentWork)">
            <el-icon><CopyDocument /></el-icon>
            复制ID
          </el-button>
          <el-button type="danger" @click="handleDelete(currentWork)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>
    </el-drawer>

    <el-dialog v-model="videoDialogVisible" :title="currentVideo?.title || '视频播放'" width="900px" class="media-dialog">
      <div class="video-container">
        <video
          v-if="videoDialogVisible && currentVideo"
          :src="`/api/works/${currentVideo.work_id}/video`"
          controls
          autoplay
          class="video-player"
        />
        <div v-if="currentVideo" class="video-info">
          <div class="info-item">
            <el-icon><Star /></el-icon>
            <span>{{ currentVideo.digg_count || 0 }}</span>
          </div>
          <div class="info-item">
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ currentVideo.comment_count || 0 }}</span>
          </div>
          <div class="info-item">
            <el-icon><Collection /></el-icon>
            <span>{{ currentVideo.collect_count || 0 }}</span>
          </div>
          <div class="info-item">
            <el-icon><Share /></el-icon>
            <span>{{ currentVideo.share_count || 0 }}</span>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="imageDialogVisible" :title="currentImages?.title || '图集'" width="900px" class="media-dialog">
      <div class="image-viewer-container">
        <el-carousel
          v-if="currentImages?.images?.length"
          :interval="5000"
          arrow="always"
          indicator-position="outside"
          height="500px"
        >
          <el-carousel-item v-for="(img, index) in currentImages.images" :key="index">
            <div class="image-wrapper">
              <el-image
                :src="img"
                :preview-src-list="currentImages.images"
                :initial-index="index"
                fit="contain"
                class="carousel-image"
              />
            </div>
          </el-carousel-item>
        </el-carousel>

        <div v-if="currentImages?.video_url" class="music-player">
          <div class="music-info">
            <el-icon><Headset /></el-icon>
            <span>背景音乐</span>
          </div>
          <audio
            ref="audioPlayer"
            :src="`/api/works/${currentImages.work_id}/video`"
            controls
            loop
            class="audio-controls"
          />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <span class="image-count">共 {{ currentImages?.images?.length || 0 }} 张图片</span>
          <el-button @click="imageDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { worksApi, exportApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedWorks = ref([])
const collectDialogVisible = ref(false)
const collectLoading = ref(false)
const collectMode = ref('single')
const videoDialogVisible = ref(false)
const currentVideo = ref(null)
const imageDialogVisible = ref(false)
const currentImages = ref(null)
const audioPlayer = ref(null)
const detailDrawerVisible = ref(false)
const currentWork = ref(null)
const activeQuickFilter = ref('')

const queryParams = reactive({
  page: 1,
  page_size: 20,
  work_type: '',
  keyword: '',
  min_likes: null,
  max_likes: null
})

const collectForm = reactive({
  work_id: '',
  batch_ids: ''
})

const stats = ref({
  videos: 0,
  images: 0,
  totalLikes: 0,
  totalComments: 0,
  totalCollects: 0,
  totalShares: 0
})

const quickFilters = [
  { label: '全部', value: '' },
  { label: '高赞 (>1w)', value: 'high_likes' },
  { label: '最新', value: 'latest' },
  { label: '视频', value: 'video' },
  { label: '图集', value: 'image' }
]

const batchCount = computed(() => {
  if (!collectForm.batch_ids) return 0
  return collectForm.batch_ids.split('\n').filter(line => line.trim()).length
})

const loadStats = async () => {
  try {
    const res = await worksApi.stats()
    stats.value = {
      videos: res.data.videos,
      images: res.data.images,
      totalLikes: res.data.total_likes,
      totalComments: res.data.total_comments,
      totalCollects: res.data.total_collects,
      totalShares: res.data.total_shares
    }
  } catch (e) {
    console.error('加载统计失败')
  }
}

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

const applyQuickFilter = (filter) => {
  activeQuickFilter.value = filter
  queryParams.work_type = ''
  queryParams.min_likes = null
  queryParams.max_likes = null
  
  switch (filter) {
    case 'high_likes':
      queryParams.min_likes = 10000
      break
    case 'video':
    case 'image':
      queryParams.work_type = filter
      break
    case 'latest':
      break
  }
  queryParams.page = 1
  loadData()
}

const handleCollect = () => {
  collectForm.work_id = ''
  collectForm.batch_ids = ''
  collectMode.value = 'single'
  collectDialogVisible.value = true
}

const submitCollect = async () => {
  if (collectMode.value === 'single') {
    if (!collectForm.work_id) {
      ElMessage.warning('请输入作品ID或链接')
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
  } else {
    if (batchCount.value === 0) {
      ElMessage.warning('请输入至少一个作品ID')
      return
    }
    collectLoading.value = true
    try {
      const ids = collectForm.batch_ids.split('\n').filter(line => line.trim())
      let success = 0
      for (const id of ids) {
        try {
          await worksApi.collect(id.trim())
          success++
        } catch (e) {
          console.error('采集失败:', id)
        }
      }
      ElMessage.success(`成功创建 ${success} 个采集任务`)
      collectDialogVisible.value = false
    } finally {
      collectLoading.value = false
    }
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
  queryParams.min_likes = null
  queryParams.max_likes = null
  queryParams.page = 1
  activeQuickFilter.value = ''
  loadData()
}

const handleSelectionChange = (selection) => {
  selectedWorks.value = selection
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedWorks.value.length} 个作品吗？`, '确认删除', { type: 'warning' })
    const ids = selectedWorks.value.map(w => w.work_id)
    for (const id of ids) {
      await worksApi.delete(id)
    }
    ElMessage.success('批量删除成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const showDetail = (row) => {
  currentWork.value = row
  detailDrawerVisible.value = true
}

const handleCommand = (command, row) => {
  switch (command) {
    case 'open':
      openWorkUrl(row)
      break
    case 'copy':
      copyWorkId(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

const openWorkUrl = (row) => {
  if (row.work_url) {
    window.open(row.work_url, '_blank')
  }
}

const openUserUrl = (row) => {
  if (row.user_url) {
    window.open(row.user_url, '_blank')
  }
}

const copyWorkId = async (row) => {
  try {
    await navigator.clipboard.writeText(row.work_id)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该作品吗？', '确认删除', { type: 'warning' })
    await worksApi.delete(row.work_id)
    ElMessage.success('删除成功')
    detailDrawerVisible.value = false
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const formatDate = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }) + ' ' + 
         date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

const playVideo = (row) => {
  currentVideo.value = row
  videoDialogVisible.value = true
}

const viewImages = (row) => {
  currentImages.value = row
  imageDialogVisible.value = true
}

watch(imageDialogVisible, (val) => {
  if (!val && audioPlayer.value) {
    audioPlayer.value.pause()
  }
})

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.works-page {
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

.stat-icon.video { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.stat-icon.image { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.stat-icon.likes { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.stat-icon.comments { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.stat-icon.collects { background: rgba(254, 44, 85, 0.15); color: #ff6b8a; }
.stat-icon.shares { background: rgba(37, 244, 238, 0.15); color: #00d4aa; }

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

.filter-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-item label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.filter-item .el-select,
.filter-item .el-input {
  width: 180px;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-inputs .el-input-number {
  width: 100px;
}

.range-separator {
  color: var(--text-muted);
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.table-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.cover-cell {
  width: 72px;
  height: 54px;
  position: relative;
  cursor: pointer;
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.cover-image {
  width: 100%;
  height: 100%;
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

.play-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  opacity: 0;
  transition: opacity 0.2s;
}

.cover-cell:hover .play-overlay {
  opacity: 1;
}

.title-cell {
  cursor: pointer;
}

.title-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
  margin-bottom: 6px;
}

.title-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.work-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}

.author-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.author-avatar {
  flex-shrink: 0;
  background: var(--bg-tertiary);
}

.author-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.author-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.interaction-stats-vertical {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.interaction-stats-vertical .stat-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.interaction-stats-vertical .stat-icon {
  font-size: 14px;
}

.interaction-stats-vertical .stat-icon.like { color: var(--accent-primary); }
.interaction-stats-vertical .stat-icon.comment { color: var(--accent-secondary); }
.interaction-stats-vertical .stat-icon.collect { color: #ff6b8a; }

.interaction-stats-vertical .stat-num {
  font-size: 12px;
  color: var(--text-secondary);
}

.time-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
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

.collect-dialog {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.collect-mode {
  width: 100%;
}

.collect-mode .el-radio-button {
  flex: 1;
}

.single-input,
.batch-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.batch-tips {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-drawer .detail-content {
  padding: 0 20px;
}

.detail-cover {
  position: relative;
  width: 100%;
  height: 300px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 20px;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.play-btn {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: white;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.detail-cover:hover .play-btn {
  opacity: 1;
}

.detail-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.stat-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.stat-box .stat-icon {
  width: 36px;
  height: 36px;
  font-size: 18px;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
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

.author-detail {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.author-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.author-detail .author-name {
  font-size: 15px;
  font-weight: 500;
}

.author-id {
  font-size: 12px;
  color: var(--text-muted);
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.preview-img {
  width: 100%;
  height: 100px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.more-images {
  width: 100%;
  height: 100px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.media-dialog .video-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-player {
  width: 100%;
  max-height: 500px;
  border-radius: var(--radius-lg);
  background: #000;
}

.video-info {
  display: flex;
  justify-content: center;
  gap: 32px;
}

.video-info .info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
}

.video-info .info-item .el-icon {
  color: var(--accent-primary);
}

.image-viewer-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.carousel-image {
  width: 100%;
  height: 100%;
}

.music-player {
  background: var(--accent-gradient);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.music-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  font-weight: 500;
  min-width: 100px;
}

.audio-controls {
  flex: 1;
  height: 36px;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.image-count {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
