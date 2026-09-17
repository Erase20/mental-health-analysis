import request from '@/utils/request'

export function getOverview() {
  return request({
    url: '/viz/overview',
    method: 'get'
  })
}

export function getRiskAnalysis() {
  return request({
    url: '/viz/risk-analysis',
    method: 'get'
  })
}

export function getClusterAnalysis() {
  return request({
    url: '/viz/cluster-analysis',
    method: 'get'
  })
}

export function getFeatureAnalysis() {
  return request({
    url: '/viz/feature-analysis',
    method: 'get'
  })
}

export function getCorrelation() {
  return request({
    url: '/viz/correlation',
    method: 'get'
  })
}

export function getGeoDistribution() {
  return request({
    url: '/viz/geo-distribution',
    method: 'get'
  })
}

export function getTrend() {
  return request({
    url: '/viz/trend',
    method: 'get'
  })
}

export function getRadar(params) {
  return request({
    url: '/viz/radar',
    method: 'get',
    params
  })
}

export function getComparison(params) {
  return request({
    url: '/viz/comparison',
    method: 'get',
    params
  })
}
