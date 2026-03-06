<template>
  <el-container class="app-container">
    <el-header class="header">
      <div class="logo">抖音爬虫管理系统</div>
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        :ellipsis="false"
        router
      >
        <el-menu-item index="/works">作品</el-menu-item>
        <el-menu-item index="/users">用户</el-menu-item>
        <el-menu-item index="/search">搜索</el-menu-item>
        <el-menu-item index="/live">直播</el-menu-item>
        <el-menu-item index="/tasks">任务</el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app-container {
  height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.logo {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
  margin-right: 40px;
}

.el-menu {
  flex: 1;
  border-bottom: none !important;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
}
</style>
