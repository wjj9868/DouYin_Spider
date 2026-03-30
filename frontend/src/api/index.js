import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.response.use(
  res => res.data,
  err => {
    console.error(err)
    return Promise.reject(err)
  }
)

export const worksApi = {
  list: (params) => request.get('/works', { params }),
  get: (workId) => request.get(`/works/${workId}`),
  create: (data) => request.post('/works', data),
  update: (workId, data) => request.put(`/works/${workId}`, data),
  delete: (workId) => request.delete(`/works/${workId}`),
  batchDelete: (workIds) => request.delete('/works/batch', { data: { work_ids: workIds } }),
  collect: (workId) => request.post('/works/collect', null, { params: { work_id: workId } }),
  getComments: (workId, params) => request.get(`/works/${workId}/comments`, { params }),
  stats: () => request.get('/works/stats')
}

export const usersApi = {
  list: (params) => request.get('/users', { params }),
  get: (uid) => request.get(`/users/${uid}`),
  create: (data) => request.post('/users', data),
  update: (uid, data) => request.put(`/users/${uid}`, data),
  delete: (uid) => request.delete(`/users/${uid}`),
  batchDelete: (uids) => request.delete('/users/batch', { data: { uids } }),
  getWorks: (uid, params) => request.get(`/users/${uid}/works`, { params }),
  collect: (uid) => request.post(`/users/${uid}/collect`),
  collectWorks: (uid, secUid, maxCount) => request.post(`/users/${uid}/collect-works`, null, { params: { sec_uid: secUid, max_count: maxCount } }),
  collectByUrl: (userUrl) => request.post('/users/collect-by-url', { user_url: userUrl }),
  collectBySecUid: (secUid) => request.post('/users/collect-by-sec-uid', { sec_uid: secUid }),
  searchDouyin: (keyword, num = 20) => request.post('/users/search-douyin', { keyword, num }),
  stats: () => request.get('/users/stats')
}

export const searchApi = {
  works: (params) => request.post('/search/works', params),
  users: (params) => request.post('/search/users', params),
  live: (keyword) => request.post('/search/live', null, { params: { keyword } })
}

export const tasksApi = {
  list: (params) => request.get('/tasks', { params }),
  get: (taskId) => request.get(`/tasks/${taskId}`),
  create: (data) => request.post('/tasks', data),
  delete: (taskId) => request.delete(`/tasks/${taskId}`),
  batchDelete: (ids) => request.delete('/tasks/batch', { data: { ids } }),
  cancel: (taskId) => request.post(`/tasks/${taskId}/cancel`),
  retry: (taskId) => request.post(`/tasks/${taskId}/retry`),
  stats: () => request.get('/tasks/stats')
}

export const scheduledTasksApi = {
  list: (params) => request.get('/scheduled-tasks', { params }),
  get: (taskId) => request.get(`/scheduled-tasks/${taskId}`),
  create: (data) => request.post('/scheduled-tasks', data),
  update: (taskId, data) => request.put(`/scheduled-tasks/${taskId}`, data),
  delete: (taskId) => request.delete(`/scheduled-tasks/${taskId}`),
  toggle: (taskId) => request.post(`/scheduled-tasks/${taskId}/toggle`),
  runNow: (taskId) => request.post(`/scheduled-tasks/${taskId}/run-now`)
}

export const exportApi = {
  works: (params) => request.get('/export/works', { params, responseType: 'blob' }),
  users: (params) => request.get('/export/users', { params, responseType: 'blob' }),
  comments: (params) => request.get('/export/comments', { params, responseType: 'blob' })
}

export const liveApi = {
  list: (params) => request.get('/live/rooms', { params }),
  start: (roomId) => request.post(`/live/rooms/${roomId}/start`),
  stop: (roomId) => request.post(`/live/rooms/${roomId}/stop`)
}

export const cookiesApi = {
  list: (params) => request.get('/cookies', { params }),
  get: (id) => request.get(`/cookies/${id}`),
  create: (data) => request.post('/cookies', data),
  update: (id, data) => request.put(`/cookies/${id}`, data),
  delete: (id) => request.delete(`/cookies/${id}`),
  verify: (id) => request.post(`/cookies/${id}/verify`),
  activate: (id) => request.post(`/cookies/${id}/activate`),
  getTypes: () => request.get('/cookies/types'),
  getStats: () => request.get('/cookies/stats'),
  getActiveByType: (type) => request.get(`/cookies/active/${type}`)
}

export const followersApi = {
  getFollowers: (secUid, params) => request.get(`/users/${secUid}/followers`, { params }),
  getFollowings: (secUid, params) => request.get(`/users/${secUid}/followings`, { params }),
  collectFollowers: (secUid) => request.post(`/users/${secUid}/collect-followers`),
  collectFollowings: (secUid) => request.post(`/users/${secUid}/collect-followings`)
}

export const commentsApi = {
  list: (workId, params) => request.get(`/works/${workId}/comments`, { params }),
  getReplies: (workId, commentId, params) => request.get(`/works/${workId}/comments/${commentId}/replies`, { params }),
  collect: (workId, maxCount) => request.post(`/works/${workId}/collect-comments`, null, { params: { max_count: maxCount } })
}

export default request
