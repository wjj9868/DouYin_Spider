<template>
  <div class="app-wrapper">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed, mobile: isMobile, open: mobileMenuOpen }">
      <div class="logo-section">
        <div class="logo-icon">
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
        <div class="logo-text" v-show="!sidebarCollapsed || isMobile">
          <span class="logo-title">Douyin Spider</span>
          <span class="logo-subtitle">数据采集系统</span>
        </div>
        <button class="collapse-btn" @click="toggleSidebar" v-if="!isMobile">
          <el-icon>
            <component :is="sidebarCollapsed ? 'Expand' : 'Fold'" />
          </el-icon>
        </button>
      </div>

      <nav class="nav-menu">
        <router-link to="/works" class="nav-item" :class="{ active: activeMenu === '/works' }" @click="closeMobileMenu">
          <el-icon><VideoPlay /></el-icon>
          <span v-show="!sidebarCollapsed || isMobile">作品管理</span>
          <div class="nav-indicator"></div>
        </router-link>

        <router-link to="/users" class="nav-item" :class="{ active: activeMenu === '/users' }" @click="closeMobileMenu">
          <el-icon><User /></el-icon>
          <span v-show="!sidebarCollapsed || isMobile">用户管理</span>
          <div class="nav-indicator"></div>
        </router-link>

<!--        <router-link to="/followers" class="nav-item" :class="{ active: activeMenu === '/followers' }" @click="closeMobileMenu">-->
<!--          <el-icon><UserFilled /></el-icon>-->
<!--          <span v-show="!sidebarCollapsed || isMobile">粉丝关注</span>-->
<!--          <div class="nav-indicator"></div>-->
<!--        </router-link>-->

        <router-link to="/comments" class="nav-item" :class="{ active: activeMenu === '/comments' }" @click="closeMobileMenu">
          <el-icon><ChatDotRound /></el-icon>
          <span v-show="!sidebarCollapsed || isMobile">作品评论</span>
          <div class="nav-indicator"></div>
        </router-link>

        <router-link to="/search" class="nav-item" :class="{ active: activeMenu === '/search' }" @click="closeMobileMenu">
          <el-icon><Search /></el-icon>
          <span v-show="!sidebarCollapsed || isMobile">搜索采集</span>
          <div class="nav-indicator"></div>
        </router-link>

<!--        <router-link to="/live" class="nav-item" :class="{ active: activeMenu === '/live' }" @click="closeMobileMenu">-->
<!--          <el-icon><VideoCamera /></el-icon>-->
<!--          <span v-show="!sidebarCollapsed || isMobile">直播监控</span>-->
<!--          <div class="nav-indicator"></div>-->
<!--        </router-link>-->

        <div class="nav-divider" v-show="!sidebarCollapsed || isMobile"></div>

        <router-link to="/tasks" class="nav-item" :class="{ active: activeMenu === '/tasks' }" @click="closeMobileMenu">
          <el-icon><List /></el-icon>
          <span v-show="!sidebarCollapsed || isMobile">任务列表</span>
          <div class="nav-indicator"></div>
        </router-link>

        <router-link to="/scheduled-tasks" class="nav-item" :class="{ active: activeMenu === '/scheduled-tasks' }" @click="closeMobileMenu">
          <el-icon><Timer /></el-icon>
          <span v-show="!sidebarCollapsed || isMobile">定时任务</span>
          <div class="nav-indicator"></div>
        </router-link>

        <router-link to="/settings" class="nav-item" :class="{ active: activeMenu === '/settings' }" @click="closeMobileMenu">
          <el-icon><Setting /></el-icon>
          <span v-show="!sidebarCollapsed || isMobile">系统设置</span>
          <div class="nav-indicator"></div>
        </router-link>
      </nav>

      <div class="sidebar-footer" v-show="!sidebarCollapsed || isMobile">
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span>系统运行中</span>
        </div>
      </div>
    </aside>

    <div class="sidebar-overlay" v-if="isMobile && mobileMenuOpen" @click="closeMobileMenu"></div>

    <main class="main-content" :class="{ expanded: sidebarCollapsed, mobile: isMobile }">
      <header class="top-bar">
        <div class="breadcrumb">
          <button class="mobile-menu-btn" @click="toggleMobileMenu" v-if="isMobile">
            <el-icon><Menu /></el-icon>
          </button>
          <el-icon v-if="!isMobile"><Location /></el-icon>
          <span>{{ currentPageTitle }}</span>
        </div>
        <div class="top-actions" v-if="!isMobile">
          <div class="quick-stats">
            <div class="stat-item">
              <el-icon class="stat-icon"><VideoPlay /></el-icon>
              <span class="stat-value">{{ quickStats.works }}</span>
              <span class="stat-label">作品</span>
            </div>
            <div class="stat-item">
              <el-icon class="stat-icon"><User /></el-icon>
              <span class="stat-value">{{ quickStats.users }}</span>
              <span class="stat-label">用户</span>
            </div>
            <div class="stat-item">
              <el-icon class="stat-icon"><Clock /></el-icon>
              <span class="stat-value">{{ quickStats.tasks }}</span>
              <span class="stat-label">任务</span>
            </div>
          </div>
        </div>
      </header>

      <div class="content-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { worksApi, usersApi, tasksApi } from '@/api'

const route = useRoute()
const activeMenu = computed(() => route.path)

const sidebarCollapsed = ref(false)
const isMobile = ref(false)
const mobileMenuOpen = ref(false)

const quickStats = ref({
  works: 0,
  users: 0,
  tasks: 0
})

const currentPageTitle = computed(() => {
  const titles = {
    '/works': '作品管理',
    '/users': '用户管理',
    '/followers': '粉丝关注',
    '/comments': '作品评论',
    '/search': '搜索采集',
    '/live': '直播监控',
    '/tasks': '任务列表',
    '/scheduled-tasks': '定时任务',
    '/settings': '系统设置'
  }
  return titles[route.path] || '控制台'
})

const checkScreenSize = () => {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) {
    mobileMenuOpen.value = false
    sidebarCollapsed.value = false
  }
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

const closeMobileMenu = () => {
  if (isMobile.value) {
    mobileMenuOpen.value = false
  }
}

const loadQuickStats = async () => {
  try {
    const [worksRes, usersRes, tasksRes] = await Promise.all([
      worksApi.list({ page: 1, page_size: 1 }),
      usersApi.list({ page: 1, page_size: 1 }),
      tasksApi.list({ page: 1, page_size: 1 })
    ])
    quickStats.value = {
      works: worksRes.data.total || 0,
      users: usersRes.data.total || 0,
      tasks: tasksRes.data.total || 0
    }
  } catch (e) {
    console.error('Failed to load stats')
  }
}

onMounted(() => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
  loadQuickStats()
  setInterval(loadQuickStats, 60000)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<style scoped>
.app-wrapper {
  display: flex;
  min-height: 100vh;
  background: var(--bg-primary);
}

.sidebar {
  width: 220px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  transition: width 0.3s ease, transform 0.3s ease;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 12px;
}

.sidebar.mobile {
  transform: translateX(-100%);
  width: 280px;
}

.sidebar.mobile.open {
  transform: translateX(0);
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

.logo-section {
  padding: 24px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
  min-height: 72px;
}

.sidebar.collapsed .logo-section {
  padding: 24px 12px;
  justify-content: center;
}

.logo-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.logo-icon svg {
  width: 100%;
  height: 100%;
}

.logo-text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.logo-title {
  font-size: 15px;
  font-weight: 700;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
  white-space: nowrap;
}

.collapse-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: var(--accent-primary);
  color: white;
}

.nav-menu {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  position: relative;
  margin-bottom: 4px;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(254, 44, 85, 0.1);
  color: var(--accent-primary);
}

.nav-item.active .nav-indicator {
  opacity: 1;
}

.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: var(--accent-gradient);
  border-radius: 0 3px 3px 0;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.nav-item .el-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.nav-item span {
  font-size: 14px;
  font-weight: 500;
}

.sidebar.collapsed .nav-item span {
  display: none;
}

.nav-divider {
  height: 1px;
  background: var(--border-color);
  margin: 16px 0;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #00d4aa;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.main-content {
  flex: 1;
  margin-left: 220px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left 0.3s ease;
  overflow-x: hidden;
  width: calc(100vw - 220px);
}

.main-content.expanded {
  margin-left: 64px;
  width: calc(100vw - 64px);
}

.main-content.mobile {
  margin-left: 0;
  width: 100vw;
}

.top-bar {
  height: 64px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.breadcrumb .el-icon {
  color: var(--accent-primary);
}

.mobile-menu-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 8px;
}

.quick-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.stat-icon {
  color: var(--accent-primary);
  font-size: 16px;
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.content-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1200px) {
  .quick-stats {
    gap: 12px;
  }
  
  .stat-item {
    padding: 6px 12px;
  }
}

@media (max-width: 992px) {
  .sidebar {
    width: 180px;
  }
  
  .main-content {
    margin-left: 180px;
    width: calc(100vw - 180px);
  }
  
  .main-content.expanded {
    margin-left: 64px;
    width: calc(100vw - 64px);
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 240px;
  }
  
  .main-content {
    margin-left: 0;
    width: 100vw;
  }
  
  .top-bar {
    padding: 0 16px;
  }
  
  .content-area {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .logo-title {
    font-size: 14px;
  }
  
  .content-area {
    padding: 12px;
  }
}
</style>
