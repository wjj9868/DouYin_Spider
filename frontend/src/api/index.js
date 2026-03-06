import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 响应拦截
request.interceptors.response.use(
  res => res.data,
  err => {
    console.error(err)
    return Promise.reject(err)
  }
)

// 作品 API
export const worksApi = {
  list: (params) => request.get('/works', { params }),
  get: (workId) => request.get(`/works/${workId}`),
  collect: (workId) => request.post('/works/collect', null, { params: { work_id: workId } }),
  getComments: (workId, params) => request.get(`/works/${workId}/comments`, { params })
}

// 用户 API
export const usersApi = {
  list: (params) => request.get('/users', { params }),
  get: (uid) => request.get(`/users/${uid}`),
  getWorks: (uid, params) => request.get(`/users/${uid}/works`, { params }),
  collect: (uid) => request.post(`/users/${uid}/collect`),
  collectWorks: (uid, secUid, maxCount) => request.post(`/users/${uid}/collect-works`, null, { params: { sec_uid: secUid, max_count: maxCount } })
}

// 搜索 API
export const searchApi = {
  works: (keyword, maxCount) => request.post('/search/works', null, { params: { keyword, max_count: maxCount } }),
  users: (keyword) => request.post('/search/users', null, { params: { keyword } }),
  live: (keyword) => request.post('/search/live', null, { params: { keyword } })
}

// 任务 API
export const tasksApi = {
  list: (params) => request.get('/tasks', { params }),
  get: (taskId) => request.get(`/tasks/${taskId}`),
  create: (data) => request.post('/tasks', data),
  delete: (taskId) => request.delete(`/tasks/${taskId}`),
  cancel: (taskId) => request.post(`/tasks/${taskId}/cancel`)
}

// 导出 API
export const exportApi = {
  works: (params) => request.get('/export/works', { params, responseType: 'blob' }),
  users: (params) => request.get('/export/users', { params, responseType: 'blob' }),
  comments: (params) => request.get('/export/comments', { params, responseType: 'blob' })
}

// 直播 API
export const liveApi = {
  list: (params) => request.get('/live/rooms', { params }),
  start: (roomId) => request.post(`/live/rooms/${roomId}/start`),
  stop: (roomId) => request.post(`/live/rooms/${roomId}/stop`)
}

export default request
