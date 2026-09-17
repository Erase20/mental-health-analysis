<template>
  <div class="dashboard-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-title">总样本数</div>
          <div class="stat-value">{{ overviewData.total_samples || 0 }}</div>
          <div class="stat-desc">心理健康调查数据</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-card-warning">
          <div class="stat-title">高风险人数</div>
          <div class="stat-value">{{ overviewData.risk_distribution?.['High Risk'] || 0 }}</div>
          <div class="stat-desc">需要重点关注</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-card-success">
          <div class="stat-title">低风险人数</div>
          <div class="stat-value">{{ overviewData.risk_distribution?.['Low Risk'] || 0 }}</div>
          <div class="stat-desc">心理健康状况良好</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-card-info">
          <div class="stat-title">聚类群体数</div>
          <div class="stat-value">{{ Object.keys(overviewData.cluster_distribution || {}).length }}</div>
          <div class="stat-desc">K-Means++聚类结果</div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">风险等级分布</span>
          </div>
          <v-chart class="chart-container" :option="riskPieOption" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">性别分布</span>
          </div>
          <v-chart class="chart-container" :option="genderPieOption" autoresize />
        </div>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">年龄分布</span>
          </div>
          <v-chart class="chart-container" :option="ageBarOption" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">聚类分布</span>
          </div>
          <v-chart class="chart-container" :option="clusterBarOption" autoresize />
        </div>
      </el-col>
    </el-row>
    
    <!-- 国家分布 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="24">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">国家分布 (Top 10)</span>
          </div>
          <v-chart class="chart-container" :option="countryBarOption" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import { getOverview } from '@/api/visualization'

const overviewData = ref({})

// 风险等级饼图配置
const riskPieOption = computed(() => {
  const data = overviewData.value.risk_distribution || {}
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%' },
    color: ['#67c23a', '#e6a23c', '#f56c6c'],
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      data: Object.entries(data).map(([name, value]) => ({ name, value }))
    }]
  }
})

// 性别饼图配置
const genderPieOption = computed(() => {
  const data = overviewData.value.gender_distribution || {}
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%' },
    color: ['#409eff', '#e91e63', '#9c27b0', '#607d8b'],
    series: [{
      type: 'pie',
      radius: '60%',
      data: Object.entries(data).map(([name, value]) => ({ name, value })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
})

// 年龄柱状图配置
const ageBarOption = computed(() => {
  const data = overviewData.value.age_distribution || {}
  const categories = Object.keys(data)
  const values = Object.values(data)
  
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { rotate: 30 }
    },
    yAxis: { type: 'value' },
    series: [{
      data: values,
      type: 'bar',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      barWidth: '50%'
    }]
  }
})

// 聚类柱状图配置
const clusterBarOption = computed(() => {
  const data = overviewData.value.cluster_distribution || {}
  const categories = Object.keys(data)
  const values = Object.values(data)
  
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories
    },
    yAxis: { type: 'value' },
    series: [{
      data: values,
      type: 'bar',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#f093fb' },
          { offset: 1, color: '#f5576c' }
        ])
      },
      barWidth: '50%'
    }]
  }
})

// 国家柱状图配置
const countryBarOption = computed(() => {
  const data = overviewData.value.country_distribution || {}
  const categories = Object.keys(data)
  const values = Object.values(data)
  
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: categories.reverse()
    },
    series: [{
      data: values.reverse(),
      type: 'bar',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
          { offset: 0, color: '#667eea' },
          { offset: 1, color: '#764ba2' }
        ])
      },
      barWidth: '60%',
      label: {
        show: true,
        position: 'right'
      }
    }]
  }
})

const fetchData = async () => {
  try {
    const res = await getOverview()
    if (res.code === 200) {
      overviewData.value = res.data
    }
  } catch (error) {
    console.error('获取数据失败:', error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  .stat-row {
    margin-bottom: 20px;
  }
  
  .chart-row {
    margin-bottom: 20px;
  }
}
</style>
