import request from '@/utils/request'

/**
 * 获取用户画像列表
 */
export function getProfiles(params) {
  return request({
    url: '/user/profiles',
    method: 'get',
    params
  })
}

/**
 * 获取用户画像详情
 */
export function getProfileDetail(id) {
  return request({
    url: `/user/profiles/${id}`,
    method: 'get'
  })
}

/**
 * 搜索用户画像
 */
export function searchProfiles(params) {
  return request({
    url: '/user/profiles/search',
    method: 'get',
    params
  })
}

/**
 * 获取相似画像
 */
export function getSimilarProfiles(id, params) {
  return request({
    url: `/user/profiles/${id}/similar`,
    method: 'get',
    params
  })
}

/**
 * 获取画像统计
 */
export function getProfileStatistics() {
  return request({
    url: '/user/profiles/statistics',
    method: 'get'
  })
}

/**
 * 用户自评 - 填写特征值查看画像和风险
 */
export function submitSelfAssessment(data) {
  return request({
    url: '/user/self-assessment',
    method: 'post',
    data
  })
}

/**
 * 获取自评记录列表
 */
export function getAssessmentRecords(params) {
  return request({
    url: '/user/assessment-records',
    method: 'get',
    params
  })
}

/**
 * 获取自评记录详情
 */
export function getAssessmentDetail(id) {
  return request({
    url: `/user/assessment-records/${id}`,
    method: 'get'
  })
}

/**
 * 获取自评统计数据
 */
export function getAssessmentStats() {
  return request({
    url: '/user/assessment-records/stats',
    method: 'get'
  })
}

/**
 * 获取用户账号列表（管理员）
 */
export function getUserAccounts(params) {
  return request({
    url: '/user/accounts',
    method: 'get',
    params
  })
}

/**
 * 删除用户账号（管理员）
 */
export function deleteUserAccount(userId) {
  return request({
    url: `/user/accounts/${userId}`,
    method: 'delete'
  })
}

/**
 * 启用/禁用用户账号（管理员）
 */
export function toggleUserStatus(userId) {
  return request({
    url: `/user/accounts/${userId}/toggle-status`,
    method: 'put'
  })
}
