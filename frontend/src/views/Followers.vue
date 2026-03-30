<template>
  <div class="followers-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">粉丝与关注</h1>
        <p class="page-desc">查看和管理用户的粉丝与关注列表</p>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
      </div>
    </div>

    <div class="stats-cards" v-if="selectedUser">
      <div class="stat-card">
        <div class="stat-icon followers">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(currentUserInfo.follower_count) }}</span>
          <span class="stat-label">粉丝数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon followings">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(currentUserInfo.following_count) }}</span>
          <span class="stat-label">关注数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon works">
          <el-icon><VideoPlay /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatNumber(currentUserInfo.aweme_count) }}</span>
          <span class="stat-label">作品数</span>
        </div>
      </div>
    </div>

    <div class="user-selector-section">
      <div class="selector-label">选择用户</div>
      <el-select
        v-model="selectedUser"
        placeholder="选择要查看的用户"
        filterable
        @change="handleUserChange"
        class="user-select"
      >
        <el-option
          v-for="user in userList"
          :key="user.sec_uid"
          :label="user.nickname"
          :value="user.sec_uid"
        >
          <div class="user-option">
            <el-avatar :src="user.avatar" :size="36" />
            <div class="option-info">
              <span class="option-name">{{ user.nickname }}</span>
              <span class="option-fans">{{ formatNumber(user.follower_count) }} 粉丝</span>
            </div>
          </div>
        </el-option>
      </el-select>
    </div>

    <div class="tabs-section" v-if="selectedUser">
      <div class="tabs-wrapper">
        <div
          class="tab-item"
          :class="{ active: activeTab === 'followers' }"
          @click="switchTab('followers')"
        >
          <el-icon><UserFilled /></el-icon>
          <span>粉丝列表</span>
          <span class="tab-count" v-if="followersTotal">{{ formatNumber(followersTotal) }}</span>
        </div>
        <div
          class="tab-item"
          :class="{ active: activeTab === 'followings' }"
          @click="switchTab('followings')"
        >
          <el-icon><User /></el-icon>
          <span>关注列表</span>
          <span class="tab-count" v-if="followingsTotal">{{ formatNumber(followingsTotal) }}</span>
        </div>
      </div>

      <div class="tab-actions">
        <el-button type="primary" @click="handleCollect" :loading="collecting">
          <el-icon><Download /></el-icon>
          采集{{ activeTab === 'followers' ? '粉丝' : '关注' }}
        </el-button>
        <el-button @click="loadList" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <div class="table-section" v-loading="loading">
        <el-table :data="currentList" class="modern-table" v-if="currentList.length > 0">
          <el-table-column label="用户" width="220">
            <template #default="{ row }">
              <div class="user-cell">
                <el-avatar :src="row.avatar" :size="44" class="user-avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <div class="user-info">
                  <div class="user-name">{{ row.nickname || '匿名用户' }}</div>
                  <div class="user-signature" v-if="row.signature">{{ row.signature }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="粉丝数据" width="150">
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
          <el-table-column prop="signature" label="简介" min-width="180">
            <template #default="{ row }">
              <span class="signature-text">{{ row.signature || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                circle
                @click="handleViewUser(row)"
              >
                <el-icon><Link /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="empty-state" v-else-if="!loading">
          <el-icon class="empty-icon"><UserFilled /></el-icon>
          <p>暂无{{ activeTab === 'followers' ? '粉丝' : '关注' }}数据</p>
          <el-button type="primary" @click="handleCollect">立即采集</el-button>
        </div>

        <div class="pagination-wrapper" v-if="currentList.length > 0">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="activeTab === 'followers' ? followersTotal : followingsTotal"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <div class="empty-selector" v-else>
      <el-icon class="empty-icon"><User /></el-icon>
      <p>请先选择一个用户</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { usersApi, followersApi, exportApi } from '@/api'

const selectedUser = ref('')
const userList = ref([])
const activeTab = ref('followers')
const loading = ref(false)
const collecting = ref(false)

const followersList = ref([])
const followingsList = ref([])
const followersTotal = ref(0)
const followingsTotal = ref(0)

const currentPage = ref(1)
const pageSize = ref(20)

const currentUserInfo = ref({
  follower_count: 0,
  following_count: 0,
  aweme_count: 0
})

const currentList = computed(() => {
  return activeTab.value === 'followers' ? followersList.value : followingsList.value
})

const loadUserList = async () => {
  try {
    const res = await usersApi.list({ page_size: 100 })
    if (res.code === 200 || res.code === 0) {
      userList.value = res.data.items
    }
  } catch (error) {
    console.error('加载用户列表失败', error)
  }
}

const handleUserChange = () => {
  currentPage.value = 1
  followersList.value = []
  followingsList.value = []

  // 获取当前用户信息
  const user = userList.value.find(u => u.sec_uid === selectedUser.value)
  if (user) {
    currentUserInfo.value = {
      follower_count: user.follower_count || 0,
      following_count: user.following_count || 0,
      aweme_count: user.aweme_count || 0
    }
  }

  loadList()
}

const switchTab = (tab) => {
  activeTab.value = tab
  currentPage.value = 1
  loadList()
}

const loadList = async () => {
  if (!selectedUser.value) return

  loading.value = true
  try {
    const params = { page: currentPage.value, page_size: pageSize.value }
    const apiCall = activeTab.value === 'followers'
      ? followersApi.getFollowers(selectedUser.value, params)
      : followersApi.getFollowings(selectedUser.value, params)

    const res = await apiCall
    if (res.code === 200 || res.code === 0) {
      if (activeTab.value === 'followers') {
        followersList.value = res.data.items
        followersTotal.value = res.data.total
      } else {
        followingsList.value = res.data.items
        followingsTotal.value = res.data.total
      }
    } else {
      ElMessage.error(res.message || '获取列表失败')
    }
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleCollect = async () => {
  if (!selectedUser.value) return

  collecting.value = true
  try {
    const apiCall = activeTab.value === 'followers'
      ? followersApi.collectFollowers(selectedUser.value)
      : followersApi.collectFollowings(selectedUser.value)

    const res = await apiCall
    if (res.code === 200 || res.code === 0) {
      ElMessage.success('采集任务已创建')
    } else {
      ElMessage.error(res.message || '采集失败')
    }
  } catch (error) {
    ElMessage.error('采集失败')
  } finally {
    collecting.value = false
  }
}

const handlePageChange = () => {
  loadList()
}

const handleViewUser = (item) => {
  if (item.sec_uid) {
    window.open(`https://www.douyin.com/user/${item.sec_uid}`, '_blank')
  }
}

const handleExport = async () => {
  if (!selectedUser.value) {
    ElMessage.warning('请先选择用户')
    return
  }
  ElMessage.info('导出功能开发中')
}

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

onMounted(() => {
  loadUserList()
})
</script>

<style scoped>
.followers-page {
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

.stat-icon.followers { background: rgba(254, 44, 85, 0.15); color: var(--accent-primary); }
.stat-icon.followings { background: rgba(37, 244, 238, 0.15); color: var(--accent-secondary); }
.stat-icon.works { background: rgba(255, 193, 7, 0.15); color: #ffc107; }

.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-muted); }

.user-selector-section {
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

.user-select {
  width: 100%;
  max-width: 400px;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.option-info {
  display: flex;
  flex-direction: column;
}

.option-name {
  font-size: 14px;
  color: var(--text-primary);
}

.option-fans {
  font-size: 12px;
  color: var(--text-muted);
}

.tabs-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.tabs-wrapper {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.tab-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.tab-item.active {
  background: var(--accent-gradient);
  color: white;
}

.tab-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.tab-actions {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.table-section {
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

.user-signature {
  font-size: 12px;
  color: var(--text-muted);
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.works-count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.works-count .el-icon {
  color: var(--accent-primary);
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

@media (max-width: 768px) {
  .stats-cards {
    flex-direction: column;
  }

  .tabs-wrapper {
    flex-direction: column;
  }

  .user-select {
    max-width: 100%;
  }
}
</style>
