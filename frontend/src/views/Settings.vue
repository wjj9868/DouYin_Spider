<template>
  <div class="settings-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">系统设置</h1>
        <p class="page-desc">管理 Cookie 和系统配置</p>
      </div>
    </div>

    <div class="settings-tabs">
      <div class="tab-item" :class="{ active: activeTab === 'cookies' }" @click="activeTab = 'cookies'">
        <el-icon><Key /></el-icon>
        <span>Cookie 管理</span>
      </div>
      <div class="tab-item" :class="{ active: activeTab === 'about' }" @click="activeTab = 'about'">
        <el-icon><InfoFilled /></el-icon>
        <span>关于系统</span>
      </div>
    </div>

    <div class="settings-content">
      <transition name="fade" mode="out-in">
        <div v-if="activeTab === 'cookies'" key="cookies" class="cookies-panel">
          <div class="cookie-stats">
            <div 
              v-for="stat in cookieStats" 
              :key="stat.type" 
              class="stat-card"
              :class="{ active: currentType === stat.type }"
              @click="selectType(stat.type)"
            >
              <div class="stat-icon" :class="stat.type">
                <el-icon><Key /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-name">{{ stat.name }}</div>
                <div class="stat-desc">{{ stat.desc }}</div>
                <div class="stat-count">
                  <span class="count">{{ stat.total }}</span>
                  <span class="label">个 Cookie</span>
                </div>
              </div>
              <div class="active-badge" v-if="stat.active">
                <el-icon><Check /></el-icon>
                <span>{{ stat.active.name }}</span>
              </div>
              <div class="no-active" v-else>
                <span>未设置</span>
              </div>
            </div>
          </div>

          <div class="panel-header">
            <div class="header-info">
              <h3>{{ currentTypeName }} 列表</h3>
              <p>管理 {{ currentTypeDesc }}，支持多账号切换</p>
            </div>
            <div class="header-actions">
              <el-button type="primary" @click="handleCreate">
                <el-icon><Plus /></el-icon>
                添加 Cookie
              </el-button>
              <el-button @click="loadData" :loading="loading">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>

          <div class="table-section">
            <el-table :data="tableData" v-loading="loading" class="modern-table">
              <el-table-column prop="name" label="名称" min-width="150">
                <template #default="{ row }">
                  <div class="name-cell">
                    <span>{{ row.name }}</span>
                    <el-tag v-if="row.is_active" type="success" size="small">使用中</el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="cookie_str" label="Cookie" min-width="300">
                <template #default="{ row }">
                  <div class="cookie-cell">
                    <code>{{ row.cookie_str }}</code>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="is_valid" label="状态" width="100">
                <template #default="{ row }">
                  <div class="status-badge" :class="row.is_valid ? 'valid' : 'invalid'">
                    <span class="status-dot"></span>
                    <span>{{ row.is_valid ? '有效' : '无效' }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="last_check_at" label="最后检查" width="160">
                <template #default="{ row }">
                  <span class="time-text">{{ formatTime(row.last_check_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="160">
                <template #default="{ row }">
                  <span class="time-text">{{ formatTime(row.created_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="260" fixed="right">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <el-button 
                      v-if="!row.is_active" 
                      type="success" 
                      size="small" 
                      @click="handleActivate(row)"
                    >
                      <el-icon><Check /></el-icon>
                      启用
                    </el-button>
                    <el-button type="primary" size="small" @click="handleVerify(row)" :loading="row.verifying">
                      <el-icon><RefreshRight /></el-icon>
                      验证
                    </el-button>
                    <el-button type="warning" size="small" @click="handleEdit(row)">
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
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next"
                @size-change="loadData"
                @current-change="loadData"
              />
            </div>
          </div>

          <div class="help-section">
            <h4>如何获取 Cookie</h4>
            <ol>
              <li>打开浏览器，访问 <a href="https://www.douyin.com" target="_blank">抖音网页版</a></li>
              <li>登录你的抖音账号</li>
              <li>按 F12 打开开发者工具，切换到 Network 标签</li>
              <li>刷新页面，找到任意请求</li>
              <li>在请求头中找到 Cookie 字段，复制完整内容</li>
              <li>粘贴到上方表单中保存</li>
            </ol>
          </div>
        </div>

        <div v-else key="about" class="about-panel">
          <div class="about-card">
            <div class="about-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12.53 2.28a.75.75 0 00-1.06 0L8.22 5.53a.75.75 0 001.06 1.06l2.47-2.47 2.47 2.47a.75.75 0 001.06-1.06l-3.25-3.25z" fill="url(#grad1)"/>
                <path d="M12 6.75a.75.75 0 01.75.75v9.5a.75.75 0 01-1.5 0v-9.5a.75.75 0 01.75-.75z" fill="url(#grad1)"/>
                <path d="M12 18a4.5 4.5 0 100 9 4.5 4.5 0 000-9z" fill="url(#grad2)"/>
                <defs>
                  <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#fe2c55"/>
                    <stop offset="100%" style="stop-color:#ff6b8a"/>
                  </linearGradient>
                  <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#25f4ee"/>
                    <stop offset="100%" style="stop-color:#00d4aa"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h2>Douyin Spider</h2>
            <p class="version">v2.0.0</p>
            <p class="desc">抖音数据采集系统</p>
            
            <div class="tech-stack">
              <h4>技术栈</h4>
              <div class="tech-tags">
                <el-tag>Python</el-tag>
                <el-tag>FastAPI</el-tag>
                <el-tag>Vue 3</el-tag>
                <el-tag>Element Plus</el-tag>
                <el-tag>SQLite</el-tag>
              </div>
            </div>

            <div class="features">
              <h4>功能特性</h4>
              <ul>
                <li>视频/图集作品采集</li>
                <li>用户信息采集</li>
                <li>关键词搜索采集</li>
                <li>定时任务调度</li>
                <li>数据导出 Excel</li>
                <li>直播弹幕监控</li>
              </ul>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑 Cookie' : '添加 Cookie'" width="600px" class="modern-dialog">
      <el-form :model="form" label-width="100px" class="cookie-form">
        <el-form-item label="Cookie 类型">
          <el-select 
            v-model="form.cookie_type" 
            placeholder="选择 Cookie 类型" 
            style="width: 100%"
            popper-class="cookie-type-select"
          >
            <el-option 
              v-for="t in cookieTypes" 
              :key="t.type" 
              :label="t.name" 
              :value="t.type"
            >
              <div class="type-option">
                <span class="type-name">{{ t.name }}</span>
                <span class="type-desc">{{ t.desc }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="给 Cookie 起个名字，方便识别" />
        </el-form-item>
        <el-form-item label="Cookie" required>
          <el-input 
            v-model="form.cookie_str" 
            type="textarea" 
            :rows="6" 
            placeholder="粘贴完整的 Cookie 字符串"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cookiesApi } from '@/api'

const activeTab = ref('cookies')
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const cookieTypes = ref([])
const cookieStats = ref([])
const currentType = ref('default')

const queryParams = reactive({
  page: 1,
  page_size: 20,
  cookie_type: 'default'
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const editId = ref(null)

const form = reactive({
  name: '',
  cookie_str: '',
  cookie_type: 'default'
})

const currentTypeName = computed(() => {
  const t = cookieTypes.value.find(t => t.type === currentType.value)
  return t ? t.name : 'Cookie'
})

const currentTypeDesc = computed(() => {
  const t = cookieTypes.value.find(t => t.type === currentType.value)
  return t ? t.desc : ''
})

const loadTypes = async () => {
  try {
    const res = await cookiesApi.getTypes()
    cookieTypes.value = res.data
  } catch (e) {
    console.error('加载类型失败')
  }
}

const loadStats = async () => {
  try {
    const res = await cookiesApi.getStats()
    cookieStats.value = res.data
  } catch (e) {
    console.error('加载统计失败')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await cookiesApi.list(queryParams)
    tableData.value = res.data.items.map(item => ({ ...item, verifying: false }))
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const selectType = (type) => {
  currentType.value = type
  queryParams.cookie_type = type
  queryParams.page = 1
  loadData()
}

const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  form.name = ''
  form.cookie_str = ''
  form.cookie_type = currentType.value
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.name = row.name
  form.cookie_str = ''
  form.cookie_type = row.cookie_type
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!form.name) {
    ElMessage.warning('请输入名称')
    return
  }
  if (!form.cookie_str && !isEdit.value) {
    ElMessage.warning('请输入 Cookie')
    return
  }

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await cookiesApi.update(editId.value, {
        name: form.name,
        cookie_str: form.cookie_str || undefined,
        cookie_type: form.cookie_type
      })
      ElMessage.success('更新成功')
    } else {
      await cookiesApi.create(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个 Cookie 吗？', '提示', {
      type: 'warning'
    })
    await cookiesApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleActivate = async (row) => {
  try {
    await cookiesApi.activate(row.id)
    ElMessage.success('Cookie 已启用')
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error('启用失败')
  }
}

const handleVerify = async (row) => {
  row.verifying = true
  try {
    const res = await cookiesApi.verify(row.id)
    if (res.data.is_valid) {
      ElMessage.success('Cookie 有效')
    } else {
      ElMessage.warning('Cookie 无效: ' + res.data.error_msg)
    }
    loadData()
  } catch (e) {
    ElMessage.error('验证失败')
  } finally {
    row.verifying = false
  }
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

onMounted(() => {
  loadTypes()
  loadStats()
  loadData()
})
</script>

<style scoped>
.settings-page {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.page-desc {
  font-size: 14px;
  color: var(--text-muted);
}

.settings-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 16px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.tab-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.tab-item.active {
  background: rgba(254, 44, 85, 0.1);
  color: var(--accent-primary);
}

.settings-content {
  min-height: 400px;
}

.cookie-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.cookie-stats .stat-card {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.cookie-stats .stat-card:hover {
  border-color: var(--accent-primary);
}

.cookie-stats .stat-card.active {
  border-color: var(--accent-primary);
  background: rgba(254, 44, 85, 0.05);
}

.stat-card .stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  font-size: 24px;
}

.stat-card .stat-icon.default {
  background: rgba(254, 44, 85, 0.15);
  color: var(--accent-primary);
}

.stat-card .stat-icon.live {
  background: rgba(37, 244, 238, 0.15);
  color: #25f4ee;
}

.stat-card .stat-info .stat-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stat-card .stat-info .stat-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.stat-card .stat-info .stat-count {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat-card .stat-info .count {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-card .stat-info .label {
  font-size: 12px;
  color: var(--text-muted);
}

.stat-card .active-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(37, 244, 238, 0.15);
  color: #25f4ee;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.stat-card .no-active {
  position: absolute;
  top: 16px;
  right: 16px;
  padding: 4px 10px;
  background: rgba(255, 71, 87, 0.15);
  color: #ff6b7a;
  border-radius: 20px;
  font-size: 12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-info h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.header-info p {
  font-size: 14px;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.table-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 24px;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cookie-cell code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.valid {
  background: rgba(37, 244, 238, 0.15);
  color: #25f4ee;
}

.status-badge.invalid {
  background: rgba(255, 71, 87, 0.15);
  color: #ff6b7a;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.time-text {
  font-size: 13px;
  color: var(--text-muted);
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.help-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.help-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.help-section ol {
  padding-left: 20px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.help-section a {
  color: var(--accent-primary);
  text-decoration: none;
}

.help-section a:hover {
  text-decoration: underline;
}

.about-panel {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.about-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 40px;
  text-align: center;
  max-width: 500px;
  width: 100%;
}

.about-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
}

.about-icon svg {
  width: 100%;
  height: 100%;
}

.about-card h2 {
  font-size: 28px;
  font-weight: 700;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.version {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.desc {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.tech-stack,
.features {
  text-align: left;
  margin-bottom: 24px;
}

.tech-stack h4,
.features h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.features ul {
  padding-left: 20px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.cookie-form {
  padding: 10px 0;
}

.type-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.type-option .type-name {
  font-weight: 500;
}

.type-option .type-desc {
  font-size: 12px;
  color: var(--text-muted);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
