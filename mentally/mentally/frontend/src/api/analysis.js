import request from '@/utils/request'

export function runFullAnalysis() {
  return request({
    url: '/analysis/run',
    method: 'post'
  })
}

export function runClustering() {
  return request({
    url: '/analysis/clustering',
    method: 'post'
  })
}

export function runClassification() {
  return request({
    url: '/analysis/classification',
    method: 'post'
  })
}

export function predictRisk(data) {
  return request({
    url: '/analysis/predict',
    method: 'post',
    data
  })
}

export function getAnalysisHistory(params) {
  return request({
    url: '/analysis/history',
    method: 'get',
    params
  })
}

export function getLatestAnalysis(type) {
  return request({
    url: `/analysis/latest/${type}`,
    method: 'get'
  })
}
