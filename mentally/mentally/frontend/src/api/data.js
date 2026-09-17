import request from '@/utils/request'

/**
 * 获取数据列表
 */
export function getDataList(params) {
  return request({
    url: '/data/list',
    method: 'get',
    params
  })
}

/**
 * 获取数据详情
 */
export function getDataDetail(id) {
  return request({
    url: `/data/${id}`,
    method: 'get'
  })
}

/**
 * 删除数据
 */
export function deleteData(id) {
  return request({
    url: `/data/${id}`,
    method: 'delete'
  })
}

/**
 * 上传文件
 */
export function uploadFile(data) {
  return request({
    url: '/data/upload',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 导出数据
 */
export function exportData(params) {
  return request({
    url: '/data/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

/**
 * 获取统计信息
 */
export function getStatistics() {
  return request({
    url: '/data/statistics',
    method: 'get'
  })
}
