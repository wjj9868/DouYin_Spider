<template>
  <div class="search-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">搜索采集</h1>
        <p class="page-desc">搜索抖音作品和用户数据</p>
      </div>
      <div class="header-stats">
        <div class="stat-badge">
          <el-icon><VideoPlay /></el-icon>
          <span>{{ stats.works }} 作品</span>
        </div>
        <div class="stat-badge">
          <el-icon><User /></el-icon>
          <span>{{ stats.users }} 用户</span>
        </div>
      </div>
    </div>

    <div class="search-container">
      <div class="search-tabs">
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'works' }"
          @click="activeTab = 'works'"
        >
          <el-icon><VideoPlay /></el-icon>
          <span>搜索作品</span>
        </div>
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'users' }"
          @click="activeTab = 'users'"
        >
          <el-icon><User /></el-icon>
          <span>搜索用户</span>
        </div>
      </div>

      <div class="search-content">
        <transition name="fade" mode="out-in">
          <div v-if="activeTab === 'works'" key="works" class="search-panel">
            <div class="panel-header">
              <h3>作品搜索</h3>
              <p>搜索抖音视频和图集作品</p>
            </div>

            <div class="search-form">
              <div class="form-section">
                <div class="section-title">
                  <el-icon><Search /></el-icon>
                  <span>基本条件</span>
                </div>
                <div class="form-grid">
                  <div class="form-item large">
                    <label>关键词</label>
                    <el-input 
                      v-model="worksForm.keyword" 
                      placeholder="输入搜索关键词..."
                      size="large"
                    >
                      <template #prefix>
                        <el-icon><Search /></el-icon>
                      </template>
                    </el-input>
                  </div>
                  <div class="form-item">
                    <label>采集数量</label>
                    <el-input-number 
                      v-model="worksForm.max_count" 
                      :min="1" 
                      :max="200"
                      size="large"
                      style="width: 100%"
                    />
                  </div>
                  <div class="form-item">
                    <label>排序方式</label>
                    <el-select v-model="worksForm.sort_type" size="large" style="width: 100%">
                      <el-option label="综合排序" value="0" />
                      <el-option label="最多点赞" value="1" />
                      <el-option label="最新发布" value="2" />
                    </el-select>
                  </div>
                </div>
              </div>

              <div class="form-section">
                <div class="section-title">
                  <el-icon><Filter /></el-icon>
                  <span>筛选条件</span>
                </div>
                <div class="form-grid">
                  <div class="form-item">
                    <label>发布时间</label>
                    <el-select v-model="worksForm.publish_time" size="large" style="width: 100%">
                      <el-option label="不限" value="0" />
                      <el-option label="一天内" value="1" />
                      <el-option label="一周内" value="7" />
                      <el-option label="半年内" value="180" />
                    </el-select>
                  </div>
                  <div class="form-item">
                    <label>视频时长</label>
                    <el-select v-model="worksForm.filter_duration" size="large" style="width: 100%">
                      <el-option label="不限" value="" />
                      <el-option label="一分钟内" value="0-1" />
                      <el-option label="1-5分钟" value="1-5" />
                      <el-option label="5分钟以上" value="5-10000" />
                    </el-select>
                  </div>
                  <div class="form-item">
                    <label>内容形式</label>
                    <el-select v-model="worksForm.content_type" size="large" style="width: 100%">
                      <el-option label="不限" value="0" />
                      <el-option label="视频" value="1" />
                      <el-option label="图文" value="2" />
                    </el-select>
                  </div>
                  <div class="form-item">
                    <label>搜索范围</label>
                    <el-select v-model="worksForm.search_range" size="large" style="width: 100%">
                      <el-option label="不限" value="0" />
                      <el-option label="最近看过" value="1" />
                      <el-option label="还未看过" value="2" />
                      <el-option label="关注的人" value="3" />
                    </el-select>
                  </div>
                </div>
              </div>

              <div class="form-actions">
                <el-button type="primary" size="large" @click="searchWorks" :loading="worksLoading">
                  <el-icon><Search /></el-icon>
                  开始搜索采集
                </el-button>
                <el-button size="large" @click="resetWorksForm">
                  <el-icon><RefreshRight /></el-icon>
                  重置
                </el-button>
              </div>
            </div>
          </div>

          <div v-else key="users" class="search-panel">
            <div class="panel-header">
              <h3>用户搜索</h3>
              <p>搜索抖音用户信息</p>
            </div>

            <div class="search-form">
              <div class="form-section">
                <div class="section-title">
                  <el-icon><Search /></el-icon>
                  <span>基本条件</span>
                </div>
                <div class="form-grid">
                  <div class="form-item large">
                    <label>关键词</label>
                    <el-input 
                      v-model="usersForm.keyword" 
                      placeholder="输入用户昵称或ID..."
                      size="large"
                    >
                      <template #prefix>
                        <el-icon><Search /></el-icon>
                      </template>
                    </el-input>
                  </div>
                  <div class="form-item">
                    <label>搜索数量</label>
                    <el-input-number 
                      v-model="usersForm.max_count" 
                      :min="1" 
                      :max="100"
                      size="large"
                      style="width: 100%"
                    />
                  </div>
                </div>
              </div>

              <div class="form-section">
                <div class="section-title">
                  <el-icon><Filter /></el-icon>
                  <span>筛选条件</span>
                </div>
                <div class="form-grid">
                  <div class="form-item">
                    <label>粉丝数量</label>
                    <el-select v-model="usersForm.douyin_user_fans" size="large" style="width: 100%">
                      <el-option label="不限" value="" />
                      <el-option label="1k以下" value="0_1k" />
                      <el-option label="1k-1w" value="1k_1w" />
                      <el-option label="1w-10w" value="1w_10w" />
                      <el-option label="10w-100w" value="10w_100w" />
                      <el-option label="100w以上" value="100w_" />
                    </el-select>
                  </div>
                  <div class="form-item">
                    <label>用户类型</label>
                    <el-select v-model="usersForm.douyin_user_type" size="large" style="width: 100%">
                      <el-option label="不限" value="" />
                      <el-option label="普通用户" value="common_user" />
                      <el-option label="企业用户" value="enterprise_user" />
                      <el-option label="个人认证" value="personal_user" />
                    </el-select>
                  </div>
                </div>
              </div>

              <div class="form-actions">
                <el-button type="primary" size="large" @click="searchUsers" :loading="usersLoading">
                  <el-icon><Search /></el-icon>
                  搜索用户
                </el-button>
                <el-button size="large" @click="resetUsersForm">
                  <el-icon><RefreshRight /></el-icon>
                  重置
                </el-button>
              </div>
            </div>

            <transition name="slide-up">
              <div v-if="userResults.length" class="results-section">
                <div class="results-header">
                  <h4>搜索结果</h4>
                  <span class="result-count">共 {{ userResults.length }} 个用户</span>
                </div>

                <div class="user-cards">
                  <div v-for="user in userResults" :key="user.sec_uid" class="user-card">
                    <div class="user-avatar">
                      <el-avatar :src="user.avatar" :size="60" />
                    </div>
                    <div class="user-info">
                      <div class="user-name">{{ user.nickname }}</div>
                      <div class="user-signature" v-if="user.signature">{{ user.signature }}</div>
                      <div class="user-meta">
                        <span class="meta-item">
                          <el-icon><User /></el-icon>
                          {{ formatNumber(user.follower_count) }} 粉丝
                        </span>
                        <span class="meta-item" v-if="user.aweme_count">
                          <el-icon><VideoPlay /></el-icon>
                          {{ user.aweme_count }} 作品
                        </span>
                        <span class="meta-item" v-if="user.ip_location">
                          <el-icon><Location /></el-icon>
                          {{ user.ip_location }}
                        </span>
                      </div>
                    </div>
                    <div class="user-actions">
                      <el-button type="primary" size="small" @click="collectUser(user)">
                        <el-icon><Download /></el-icon>
                        采集
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </transition>
      </div>
    </div>

    <transition name="slide-up">
      <div v-if="taskId" class="progress-section">
        <div class="progress-header">
          <h4>采集进度</h4>
          <div class="progress-status" :class="taskStatus">
            <el-icon v-if="taskStatus === 'running'" class="rotating"><Loading /></el-icon>
            <el-icon v-else-if="taskStatus === 'completed'"><CircleCheck /></el-icon>
            <el-icon v-else-if="taskStatus === 'failed'"><CircleClose /></el-icon>
            <span>{{ taskStatusText }}</span>
          </div>
        </div>

        <div class="progress-content">
          <div class="progress-bar-wrapper">
            <el-progress 
              :percentage="taskProgress" 
              :stroke-width="12"
              :status="taskStatus === 'completed' ? 'success' : taskStatus === 'failed' ? 'exception' : ''"
            />
          </div>
          <div class="progress-stats">
            <div class="stat-item">
              <el-icon><Document /></el-icon>
              <span>已采集: {{ resultCount }} 条</span>
            </div>
            <div class="stat-item" v-if="taskStatus === 'running'">
              <el-icon><Clock /></el-icon>
              <span>采集中...</span>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { searchApi, tasksApi, usersApi } from '@/api'

const activeTab = ref('works')

const stats = reactive({
  works: 0,
  users: 0
})

const worksForm = reactive({
  keyword: '',
  max_count: 50,
  sort_type: '0',
  publish_time: '0',
  filter_duration: '',
  search_range: '0',
  content_type: '0'
})

const usersForm = reactive({
  keyword: '',
  max_count: 20,
  douyin_user_fans: '',
  douyin_user_type: ''
})

const worksLoading = ref(false)
const usersLoading = ref(false)
const userResults = ref([])
const taskId = ref(null)
const taskProgress = ref(0)
const resultCount = ref(0)
const taskStatus = ref('')

let timer = null

const taskStatusText = computed(() => {
  if (taskStatus.value === 'completed') return '已完成'
  if (taskStatus.value === 'failed') return '失败'
  if (taskStatus.value === 'running') return '采集中'
  return '等待中'
})

const searchWorks = async () => {
  if (!worksForm.keyword) {
    ElMessage.warning('请输入关键词')
    return
  }
  worksLoading.value = true
  try {
    const res = await searchApi.works(worksForm)
    taskId.value = res.data.task_id
    taskProgress.value = 0
    resultCount.value = 0
    startPolling()
    ElMessage.success('搜索任务已创建')
  } catch (e) {
    ElMessage.error('创建任务失败')
  } finally {
    worksLoading.value = false
  }
}

const resetWorksForm = () => {
  worksForm.keyword = ''
  worksForm.max_count = 50
  worksForm.sort_type = '0'
  worksForm.publish_time = '0'
  worksForm.filter_duration = ''
  worksForm.search_range = '0'
  worksForm.content_type = '0'
}

const searchUsers = async () => {
  if (!usersForm.keyword) {
    ElMessage.warning('请输入关键词')
    return
  }
  usersLoading.value = true
  try {
    const res = await searchApi.users(usersForm)
    userResults.value = res.data.users || []
    if (userResults.value.length === 0) {
      ElMessage.info('未找到用户')
    }
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    usersLoading.value = false
  }
}

const resetUsersForm = () => {
  usersForm.keyword = ''
  usersForm.max_count = 20
  usersForm.douyin_user_fans = ''
  usersForm.douyin_user_type = ''
  userResults.value = []
}

const collectUser = async (user) => {
  try {
    await usersApi.collectBySecUid(user.sec_uid)
    ElMessage.success('采集任务已创建')
  } catch (e) {
    ElMessage.error('创建任务失败')
  }
}

const startPolling = () => {
  timer = setInterval(async () => {
    if (!taskId.value) return
    try {
      const res = await tasksApi.get(taskId.value)
      const task = res.data
      taskProgress.value = task.progress
      resultCount.value = task.result_count
      taskStatus.value = task.status
      if (task.status === 'completed' || task.status === 'failed') {
        clearInterval(timer)
        if (task.status === 'completed') {
          ElMessage.success('采集完成')
        } else {
          ElMessage.error('采集失败: ' + task.error_message)
        }
      }
    } catch (e) {
      clearInterval(timer)
    }
  }, 2000)
}

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.search-page {
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

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 14px;
}

.stat-badge .el-icon {
  color: var(--accent-primary);
}

.search-container {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.search-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  padding: 0 24px;
  background: var(--bg-tertiary);
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 24px;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  position: relative;
  transition: var(--transition-normal);
}

.tab-item:hover {
  color: var(--text-primary);
}

.tab-item.active {
  color: var(--accent-primary);
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 24px;
  right: 24px;
  height: 2px;
  background: var(--accent-gradient);
  border-radius: 2px;
}

.search-content {
  padding: 32px;
}

.search-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.panel-header {
  margin-bottom: 32px;
}

.panel-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.panel-header p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.section-title .el-icon {
  color: var(--accent-primary);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item.large {
  grid-column: span 2;
}

.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.results-section {
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid var(--border-color);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-header h4 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.result-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.user-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  transition: var(--transition-normal);
}

.user-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.user-avatar {
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.user-signature {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.meta-item .el-icon {
  font-size: 14px;
}

.user-actions {
  flex-shrink: 0;
}

.progress-section {
  margin-top: 24px;
  padding: 24px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.progress-header h4 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.progress-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
}

.progress-status.running {
  background: rgba(37, 244, 238, 0.1);
  color: var(--accent-secondary);
}

.progress-status.completed {
  background: rgba(0, 212, 170, 0.1);
  color: #00d4aa;
}

.progress-status.failed {
  background: rgba(254, 44, 85, 0.1);
  color: var(--accent-primary);
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.progress-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-bar-wrapper {
  margin-bottom: 8px;
}

.progress-stats {
  display: flex;
  gap: 24px;
}

.progress-stats .stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-stats .stat-item .el-icon {
  color: var(--accent-secondary);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 1200px) {
  .form-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .form-item.large {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-item.large {
    grid-column: span 1;
  }
  
  .user-cards {
    grid-template-columns: 1fr;
  }
  
  .user-card {
    flex-direction: column;
    text-align: center;
  }
  
  .user-meta {
    justify-content: center;
  }
}
</style>
