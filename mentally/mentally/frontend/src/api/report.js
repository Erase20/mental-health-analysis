import request from '@/utils/request'

/**
 * 生成报告
 */
export function generateReport(data) {
  return request({
    url: '/report/generate',
    method: 'post',
    data
  })
}

/**
 * 获取报告列表
 */
export function getReportList() {
  return request({
    url: '/report/list',
    method: 'get'
  })
}

/**
 * 下载报告
 */
export function downloadReport(filename) {
  return request({
    url: `/report/download/${filename}`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 预览报告数据
 */
export function previewReportData() {
  return request({
    url: '/report/preview',
    method: 'get'
  })
}
