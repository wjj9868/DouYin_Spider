<template>
  <div class="search-page">
    <el-card>
      <template #header>
        <span>搜索采集</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="搜索作品" name="works">
          <el-form inline>
            <el-form-item label="关键词">
              <el-input v-model="worksForm.keyword" placeholder="输入关键词" style="width: 200px" />
            </el-form-item>
            <el-form-item label="数量">
              <el-input-number v-model="worksForm.max_count" :min="1" :max="200" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="searchWorks" :loading="worksLoading">开始搜索</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="搜索用户" name="users">
          <el-form inline>
            <el-form-item label="关键词">
              <el-input v-model="usersForm.keyword" placeholder="输入关键词" style="width: 200px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="searchUsers" :loading="usersLoading">搜索</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="userResults" v-if="userResults.length" style="width: 100%; margin-top: 20px">
            <el-table-column prop="nickname" label="昵称" width="120" />
            <el-table-column prop="uid" label="用户ID" width="180" />
            <el-table-column prop="follower_count" label="粉丝" width="100" />
            <el-table-column prop="aweme_count" label="作品" width="80" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card style="margin-top: 20px" v-if="taskId">
      <template #header>
        <span>采集进度</span>
      </template>
      <el-progress :percentage="taskProgress" :status="taskStatus" />
      <div style="margin-top: 10px">
        <span>状态: {{ taskStatusText }}</span>
        <span style="margin-left: 20px">已采集: {{ resultCount }} 条</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { searchApi, tasksApi } from '@/api'

const activeTab = ref('works')
const worksForm = reactive({ keyword: '', max_count: 50 })
const usersForm = reactive({ keyword: '' })
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
    const res = await searchApi.works(worksForm.keyword, worksForm.max_count)
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

const searchUsers = async () => {
  if (!usersForm.keyword) {
    ElMessage.warning('请输入关键词')
    return
  }
  usersLoading.value = true
  try {
    const res = await searchApi.users(usersForm.keyword)
    userResults.value = res.data.users
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    usersLoading.value = false
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

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
