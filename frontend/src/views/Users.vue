<template>
  <div class="users-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">用户管理</h1>
        <p class="page-desc">管理采集的抖音用户数据</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleSearchDouyin">
          <el-icon><Search /></el-icon>
          搜索采集
        </el-button>
        <el-button type="success" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
        <el-button v-if="selectedUsers.length" type="danger" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除 ({{ selectedUsers.length }})
        </el-button>
      </div>
    </div>

    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon users">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total }}</span>
          <span class="stat-label">总用户数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon male">
          <el-icon><Male /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.male }}</span>
          <span class="stat-label">男性用户</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon female">
          <el-icon><Female /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.female }}</span>
          <span class="stat-label">女性用户</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon followers">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(stats.totalFollowers) }}</span>
          <span class="stat-label">总粉丝数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon works">
          <el-icon><VideoPlay /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(stats.totalWorks) }}</span>
          <span class="stat-label">总作品数</span>
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
          <label>关键词</label>
          <el-input v-model="queryParams.keyword" placeholder="用户ID/昵称/抖音号" clearable @keyup.enter="loadData">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <label>性别</label>
          <el-select v-model="queryParams.gender" placeholder="全部" clearable>
            <el-option label="男" :value="1" />
            <el-option label="女" :value="2" />
          </el-select>
        </div>
        <div class="filter-item">
          <label>粉丝数范围</label>
          <div class="range-inputs">
            <el-input-number v-model="queryParams.min_followers" :min="0" placeholder="最小" controls-position="right" />
            <span class="range-separator">-</span>
            <el-input-number v-model="queryParams.max_followers" :min="0" placeholder="最大" controls-position="right" />
          </div>
        </div>
        <div class="filter-actions">
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <el-table :data="tableData" v-loading="loading" @selection-change="handleSelectionChange" class="modern-table">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="avatar" label="用户" width="200">
          <template #default="{ row }">
            <div class="user-cell" @click="showDetail(row)">
              <el-avatar :src="row.avatar" :size="44" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-info">
                <div class="user-name">{{ row.nickname || '-' }}</div>
                <div class="user-id">{{ row.unique_id || row.uid?.substring(0, 12) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="粉丝数据" width="180">
          <template #default="{ row }">
            <div class="follower-stats">
              <div class="stat-row">
                <span class="stat-label">粉丝</span>
                <span class="stat-value highlight">{{ formatNumber(row.follower_count) }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">关注</span>
                <span class="stat-value">{{ formatNumber(row.following_count) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="aweme_count" label="作品" width="100">
          <template #default="{ row }">
            <div class="works-count">
              <el-icon><VideoPlay /></el-icon>
              <span>{{ row.aweme_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total_favorited" label="获赞" width="120">
          <template #default="{ row }">
            <div class="favorited-count">
              <el-icon><Star /></el-icon>
              <span>{{ formatNumber(row.total_favorited || row.favorited_count) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="gender" label="性别" width="80">
          <template #default="{ row }">
            <div class="gender-badge" :class="row.gender === 1 ? 'male' : row.gender === 2 ? 'female' : ''">
              <el-icon v-if="row.gender === 1"><Male /></el-icon>
              <el-icon v-else-if="row.gender === 2"><Female /></el-icon>
              <span v-else>-</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="ip_location" label="IP属地" width="90">
          <template #default="{ row }">
            <span class="ip-location">{{ row.ip_location || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="signature" label="简介" min-width="180">
          <template #default="{ row }">
            <span class="signature-text">{{ row.signature || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-tooltip content="查看详情" placement="top">
                <el-button type="primary" size="small" circle @click="showDetail(row)">
                  <el-icon><View /></el-icon>
                </el-button>
              </el-tooltip>
              <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
                <el-button size="small" circle>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="collect" :icon="Download">采集作品</el-dropdown-item>
                    <el-dropdown-item command="open" :icon="Link">打开主页</el-dropdown-item>
                    <el-dropdown-item command="edit" :icon="Edit">编辑</el-dropdown-item>
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

    <el-drawer v-model="detailDrawerVisible" :title="currentUser?.nickname || '用户详情'" size="550px" class="detail-drawer">
      <div v-if="currentUser" class="detail-content">
        <div class="user-header">
          <el-avatar :src="currentUser.avatar" :size="80" class="large-avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <div class="header-info">
            <div class="nickname">{{ currentUser.nickname || '未知用户' }}</div>
            <div class="unique-id">@{{ currentUser.unique_id || currentUser.uid?.substring(0, 16) }}</div>
            <div class="gender-location">
              <span v-if="currentUser.gender" class="gender" :class="currentUser.gender === 1 ? 'male' : 'female'">
                <el-icon v-if="currentUser.gender === 1"><Male /></el-icon>
                <el-icon v-else><Female /></el-icon>
                {{ currentUser.gender === 1 ? '男' : '女' }}
              </span>
              <span v-if="currentUser.ip_location" class="location">
                <el-icon><Location /></el-icon>
                {{ currentUser.ip_location }}
              </span>
            </div>
          </div>
          <el-button type="primary" @click="openUserUrl(currentUser)">
            <el-icon><Link /></el-icon>
            主页
          </el-button>
        </div>

        <div class="detail-stats">
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(currentUser.follower_count) }}</span>
            <span class="stat-label">粉丝</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(currentUser.following_count) }}</span>
            <span class="stat-label">关注</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ currentUser.aweme_count || 0 }}</span>
            <span class="stat-label">作品</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(currentUser.total_favorited || currentUser.favorited_count) }}</span>
            <span class="stat-label">获赞</span>
          </div>
        </div>

        <div class="detail-section">
          <h4>用户简介</h4>
          <p class="signature">{{ currentUser.signature || '暂无简介' }}</p>
        </div>

        <div class="detail-section">
          <h4>详细信息</h4>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">用户ID</span>
              <span class="info-value">{{ currentUser.uid }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">抖音号</span>
              <span class="info-value">{{ currentUser.unique_id || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">年龄</span>
              <span class="info-value">{{ currentUser.age ? currentUser.age + '岁' : '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">城市</span>
              <span class="info-value">{{ currentUser.city || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">采集时间</span>
              <span class="info-value">{{ formatDate(currentUser.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">更新时间</span>
              <span class="info-value">{{ formatDate(currentUser.updated_at) }}</span>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="handleCollectWorks(currentUser)">
            <el-icon><Download /></el-icon>
            采集作品
          </el-button>
          <el-button @click="handleEdit(currentUser)">
            <el-icon><Edit /></el-icon>
            编辑信息
          </el-button>
          <el-button type="danger" @click="handleDelete(currentUser)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>
    </el-drawer>

    <el-dialog v-model="editDialogVisible" title="编辑用户" width="500px" class="modern-dialog">
      <el-form :model="editForm" label-width="80px" class="edit-form">
        <el-form-item label="昵称">
          <el-input v-model="editForm.nickname" placeholder="用户昵称" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="editForm.gender">
            <el-radio :value="0">未知</el-radio>
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="年龄">
          <el-input-number v-model="editForm.age" :min="0" :max="150" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="editForm.signature" type="textarea" :rows="3" placeholder="用户简介" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="editLoading">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="searchDialogVisible" title="搜索抖音用户" width="850px" class="modern-dialog">
      <div class="search-dialog-content">
        <div class="search-input-row">
          <el-input v-model="searchKeyword" placeholder="输入用户昵称或ID搜索..." size="large" @keyup.enter="searchDouyinUsers">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" size="large" @click="searchDouyinUsers" :loading="searchLoading">
            搜索
          </el-button>
        </div>

        <div v-if="searchResults.length" class="search-results">
          <div v-for="user in searchResults" :key="user.sec_uid" class="user-card">
            <div class="user-info">
              <el-avatar :src="user.avatar" :size="50" class="user-avatar" />
              <div class="user-details">
                <div class="user-name">{{ user.nickname }}</div>
                <div class="user-signature">{{ user.signature || '暂无简介' }}</div>
                <div class="user-meta">
                  <span><el-icon><UserFilled /></el-icon> {{ formatNumber(user.follower_count) }} 粉丝</span>
                  <span><el-icon><VideoPlay /></el-icon> {{ user.aweme_count || 0 }} 作品</span>
                </div>
              </div>
            </div>
            <div class="user-actions">
              <el-tag v-if="user.is_collected" type="success" size="small">已采集</el-tag>
              <el-button v-else type="primary" size="small" @click="collectUser(user)">
                采集
              </el-button>
            </div>
          </div>
        </div>
        <div v-else-if="!searchLoading && searchKeyword" class="empty-state">
          <el-icon class="empty-icon"><Search /></el-icon>
          <p>输入关键词搜索用户</p>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="collectWorksDialogVisible" title="采集用户作品" width="450px" class="modern-dialog">
      <div class="collect-dialog-content">
        <div class="user-preview">
          <el-avatar :src="currentUser?.avatar" :size="60" />
          <div class="user-info">
            <div class="user-name">{{ currentUser?.nickname }}</div>
            <div class="user-stats">{{ formatNumber(currentUser?.follower_count) }} 粉丝</div>
          </div>
        </div>
        <el-form label-width="80px">
          <el-form-item label="采集数量">
            <el-input-number v-model="collectWorksCount" :min="1" :max="500" style="width: 100%" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="collectWorksDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCollectWorks" :loading="collectWorksLoading">开始采集</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usersApi, exportApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedUsers = ref([])
const detailDrawerVisible = ref(false)
const currentUser = ref(null)
const activeQuickFilter = ref('')

const queryParams = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  gender: null,
  min_followers: null,
  max_followers: null
})

const editDialogVisible = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  uid: '',
  nickname: '',
  gender: 0,
  age: null,
  signature: ''
})

const searchDialogVisible = ref(false)
const searchLoading = ref(false)
const searchKeyword = ref('')
const searchResults = ref([])

const collectWorksDialogVisible = ref(false)
const collectWorksLoading = ref(false)
const collectWorksCount = ref(50)

const stats = ref({
  total: 0,
  male: 0,
  female: 0,
  totalFollowers: 0,
  totalWorks: 0
})

const quickFilters = [
  { label: '全部', value: '' },
  { label: '大V (>10w粉丝)', value: 'big_v' },
  { label: '达人 (1-10w)', value: 'talent' },
  { label: '男性', value: 'male' },
  { label: '女性', value: 'female' }
]

const loadStats = async () => {
  try {
    const res = await usersApi.stats()
    stats.value = {
      total: res.data.total,
      male: res.data.male,
      female: res.data.female,
      totalFollowers: res.data.total_followers,
      totalWorks: res.data.total_works
    }
  } catch (e) {
    console.error('加载统计失败')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await usersApi.list(queryParams)
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
  queryParams.gender = null
  queryParams.min_followers = null
  queryParams.max_followers = null
  
  switch (filter) {
    case 'big_v':
      queryParams.min_followers = 100000
      break
    case 'talent':
      queryParams.min_followers = 10000
      queryParams.max_followers = 100000
      break
    case 'male':
      queryParams.gender = 1
      break
    case 'female':
      queryParams.gender = 2
      break
  }
  queryParams.page = 1
  loadData()
}

const resetQuery = () => {
  queryParams.keyword = ''
  queryParams.gender = null
  queryParams.min_followers = null
  queryParams.max_followers = null
  queryParams.page = 1
  activeQuickFilter.value = ''
  loadData()
}

const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const showDetail = (row) => {
  currentUser.value = row
  detailDrawerVisible.value = true
}

const handleCommand = (command, row) => {
  switch (command) {
    case 'collect':
      handleCollectWorks(row)
      break
    case 'open':
      openUserUrl(row)
      break
    case 'edit':
      handleEdit(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

const openUserUrl = (row) => {
  if (row.user_url) {
    window.open(row.user_url, '_blank')
  }
}

const handleEdit = (row) => {
  editForm.uid = row.uid
  editForm.nickname = row.nickname || ''
  editForm.gender = row.gender || 0
  editForm.age = row.age
  editForm.signature = row.signature || ''
  editDialogVisible.value = true
}

const submitEdit = async () => {
  editLoading.value = true
  try {
    await usersApi.update(editForm.uid, {
      nickname: editForm.nickname,
      gender: editForm.gender,
      age: editForm.age,
      signature: editForm.signature
    })
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${row.nickname}" 吗？`, '确认删除', { type: 'warning' })
    await usersApi.delete(row.uid)
    ElMessage.success('删除成功')
    detailDrawerVisible.value = false
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedUsers.value.length} 个用户吗？`, '确认删除', { type: 'warning' })
    const uids = selectedUsers.value.map(u => u.uid)
    await usersApi.batchDelete(uids)
    ElMessage.success('批量删除成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleSearchDouyin = () => {
  searchKeyword.value = ''
  searchResults.value = []
  searchDialogVisible.value = true
}

const searchDouyinUsers = async () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  searchLoading.value = true
  try {
    const res = await usersApi.searchDouyin(searchKeyword.value, 20)
    searchResults.value = res.data || []
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到用户')
    }
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    searchLoading.value = false
  }
}

const collectUser = async (row) => {
  try {
    await usersApi.collectBySecUid(row.sec_uid)
    ElMessage.success('采集任务已创建')
    searchDialogVisible.value = false
    setTimeout(() => loadData(), 1000)
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建任务失败')
  }
}

const handleCollectWorks = (row) => {
  currentUser.value = row
  collectWorksCount.value = 50
  collectWorksDialogVisible.value = true
}

const submitCollectWorks = async () => {
  if (!currentUser.value?.sec_uid) {
    ElMessage.warning('用户缺少 sec_uid 信息')
    return
  }
  collectWorksLoading.value = true
  try {
    await usersApi.collectWorks(currentUser.value.uid, currentUser.value.sec_uid, collectWorksCount.value)
    ElMessage.success('采集任务已创建')
    collectWorksDialogVisible.value = false
  } catch (e) {
    ElMessage.error('创建任务失败')
  } finally {
    collectWorksLoading.value = false
  }
}

const handleExport = async () => {
  try {
    const res = await exportApi.users({ limit: 1000 })
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `users_${Date.now()}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
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

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.users-page {
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

.stat-icon.users { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.stat-icon.male { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.stat-icon.female { background: rgba(254, 44, 85, 0.15); color: #ff6b8a; }
.stat-icon.followers { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.stat-icon.works { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }

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

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 4px 0;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-id {
  font-size: 12px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

.follower-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.follower-stats .stat-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.follower-stats .stat-label {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 28px;
}

.follower-stats .stat-value {
  font-size: 13px;
  color: var(--text-primary);
}

.follower-stats .stat-value.highlight {
  color: var(--accent-primary);
  font-weight: 600;
}

.works-count,
.favorited-count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.works-count .el-icon { color: var(--accent-primary); }
.favorited-count .el-icon { color: var(--accent-primary); }

.gender-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 14px;
}

.gender-badge.male {
  background: rgba(37, 244, 238, 0.15);
  color: var(--accent-secondary);
}

.gender-badge.female {
  background: rgba(254, 44, 85, 0.15);
  color: #ff6b8a;
}

.ip-location {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
}

.signature-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
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

.user-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-card) 100%);
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
}

.large-avatar {
  background: var(--bg-card);
  border: 3px solid var(--border-color);
}

.header-info {
  flex: 1;
  min-width: 0;
}

.nickname {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.unique-id {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.gender-location {
  display: flex;
  gap: 12px;
}

.gender-location .gender,
.gender-location .location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.gender-location .gender.male {
  background: rgba(37, 244, 238, 0.15);
  color: var(--accent-secondary);
}

.gender-location .gender.female {
  background: rgba(254, 44, 85, 0.15);
  color: #ff6b8a;
}

.gender-location .location {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.detail-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.detail-stats .stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.detail-stats .stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.detail-stats .stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
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

.signature {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin: 0;
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

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.search-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-input-row {
  display: flex;
  gap: 12px;
}

.search-input-row .el-input {
  flex: 1;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.user-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  transition: all 0.2s;
}

.user-card:hover {
  background: var(--bg-card-hover);
}

.user-card .user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-card .user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-card .user-name {
  font-size: 15px;
  font-weight: 500;
}

.user-card .user-signature {
  font-size: 12px;
  color: var(--text-muted);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-card .user-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.user-card .user-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.collect-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.user-preview {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.user-preview .user-info {
  display: flex;
  flex-direction: column;
}

.user-preview .user-name {
  font-size: 16px;
  font-weight: 500;
}

.user-preview .user-stats {
  font-size: 12px;
  color: var(--text-muted);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
</style>
