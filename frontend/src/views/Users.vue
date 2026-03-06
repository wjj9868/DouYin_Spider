<template>
  <div class="users-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <div>
            <el-button type="primary" @click="handleExport">导出Excel</el-button>
          </div>
        </div>
      </template>

      <el-form inline>
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="用户ID/昵称" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" style="width: 100%">
        <el-table-column prop="avatar" label="头像" width="70">
          <template #default="{ row }">
            <el-avatar :src="row.avatar" :size="40" />
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" width="120">
          <template #default="{ row }">
            <el-link v-if="row.user_url" :href="row.user_url" target="_blank" type="primary">
              {{ row.nickname || '-' }}
            </el-link>
            <span v-else>{{ row.nickname || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unique_id" label="抖音号" width="100" />
        <el-table-column label="粉丝/关注/作品" width="150">
          <template #default="{ row }">
            <div style="font-size: 12px;">
              <span>粉丝: {{ row.follower_count || 0 }}</span><br>
              <span>关注: {{ row.following_count || 0 }}</span><br>
              <span>作品: {{ row.aweme_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total_favorited" label="获赞" width="100">
          <template #default="{ row }">
            {{ row.total_favorited || row.favorited_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="gender" label="性别" width="60">
          <template #default="{ row }">
            <span v-if="row.gender === 1">男</span>
            <span v-else-if="row.gender === 2">女</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_location" label="IP属地" width="80" />
        <el-table-column prop="signature" label="简介" min-width="150" show-overflow-tooltip />
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
import { ElMessage } from 'element-plus'
import { usersApi, exportApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  keyword: ''
})

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

const handleExport = async () => {
  try {
    const res = await exportApi.users({ limit: 1000 })
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `users_${Date.now()}.xlsx`
    link.click()
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
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
