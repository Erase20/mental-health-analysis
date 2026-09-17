<template>
  <div class="analysis-container">
    <!-- 特征分布分析 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">特征分布分析</span>
            <el-radio-group v-model="selectedFeature" size="small">
              <el-radio-button value="treatment">治疗情况</el-radio-button>
              <el-radio-button value="family_history">家族病史</el-radio-button>
              <el-radio-button value="work_interfere">工作干扰</el-radio-button>
              <el-radio-button value="benefits">公司福利</el-radio-button>
              <el-radio-button value="remote_work">远程工作</el-radio-button>
              <el-radio-button value="tech_company">科技公司</el-radio-button>
            </el-radio-group>
          </div>
          <el-row :gutter="20">
            <el-col :xs="24" :lg="12">
              <v-chart class="chart-container" :option="featurePieOption" autoresize />
            </el-col>
            <el-col :xs="24" :lg="12">
              <v-chart class="chart-container" :option="featureBarOption" autoresize />
            </el-col>
          </el-row>
        </div>
      </el-col>
    </el-row>
    
    <!-- 风险关联分析 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">风险等级与年龄关系</span>
          </div>
          <v-chart class="chart-container" :option="riskAgeOption" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">风险等级与性别关系</span>
          </div>
          <v-chart class="chart-container" :option="riskGenderOption" autoresize />
        </div>
      </el-col>
    </el-row>
    
    <!-- 相关性热力图 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">特征相关性分析</span>
          </div>
          <v-chart class="chart-container" :option="correlationOption" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, HeatmapChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  PieChart,
  BarChart,
  HeatmapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent
])

const selectedFeature = ref('treatment')

// 静态特征分布数据
const staticFeatureData = {
  treatment_distribution: {
    'Yes': 12580,
    'No': 37355
  },
  family_history_distribution: {
    'Yes': 8988,
    'No': 40947
  },
  work_interfere_distribution: {
    'Never': 16405,
    'Rarely': 12258,
    'Sometimes': 14613,
    'Often': 6659
  },
  benefits_distribution: {
    'Yes': 18520,
    'No': 19500,
    "Don't know": 11915
  },
  remote_work_distribution: {
    'Yes': 21568,
    'No': 28367
  },
  tech_company_distribution: {
    'Yes': 32458,
    'No': 17477
  }
}

// 静态风险分析数据
const staticRiskAnalysisData = {
  risk_by_age: {
    categories: ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
    series: [
      { name: 'High Risk', data: [3256, 8934, 6234, 4123, 2156, 1095] },
      { name: 'Medium Risk', data: [1523, 3156, 2432, 1345, 786, 273] },
      { name: 'Low Risk', data: [2156, 4689, 3567, 2134, 1234, 842] }
    ]
  },
  risk_by_gender: {
    categories: ['Male', 'Female', 'Other'],
    series: [
      { name: 'High Risk', data: [14523, 11023, 252] },
      { name: 'Medium Risk', data: [5234, 4156, 125] },
      { name: 'Low Risk', data: [8234, 6234, 154] }
    ]
  }
}

// 静态相关性数据
const staticCorrelationData = {
  categories: ['年龄', '工作经验', '工作时间', '压力指数', '工作满意度', '心理健康评分'],
  data: [
    [0, 0, 1.0], [0, 1, 0.78], [0, 2, 0.32], [0, 3, -0.15], [0, 4, -0.08], [0, 5, -0.12],
    [1, 0, 0.78], [1, 1, 1.0], [1, 2, 0.45], [1, 3, -0.05], [1, 4, 0.12], [1, 5, 0.08],
    [2, 0, 0.32], [2, 1, 0.45], [2, 2, 1.0], [2, 3, 0.25], [2, 4, -0.35], [2, 5, -0.42],
    [3, 0, -0.15], [3, 1, -0.05], [3, 2, 0.25], [3, 3, 1.0], [3, 4, -0.65], [3, 5, -0.78],
    [4, 0, -0.08], [4, 1, 0.12], [4, 2, -0.35], [4, 3, -0.65], [4, 4, 1.0], [4, 5, 0.82],
    [5, 0, -0.12], [5, 1, 0.08], [5, 2, -0.42], [5, 3, -0.78], [5, 4, 0.82], [5, 5, 1.0]
  ]
}

// 特征饼图配置
const featurePieOption = computed(() => {
  const key = `${selectedFeature.value}_distribution`
  const data = staticFeatureData[key] || {}
  
  return {
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
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

// 特征柱状图配置
const featureBarOption = computed(() => {
  const key = `${selectedFeature.value}_distribution`
  const data = staticFeatureData[key] || {}
  const categories = Object.keys(data)
  const values = Object.values(data)
  
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { interval: 0, rotate: 30 }
    },
    yAxis: { type: 'value' },
    series: [{
      data: values,
      type: 'bar',
      itemStyle: {
        color: '#409eff',
        borderRadius: [4, 4, 0, 0]
      },
      barWidth: '50%'
    }]
  }
})

// 风险与年龄关系图
const riskAgeOption = computed(() => {
  const data = staticRiskAnalysisData.risk_by_age || { categories: [], series: [] }
  
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: data.series?.map(s => s.name) || [] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.categories || []
    },
    yAxis: { type: 'value' },
    series: (data.series || []).map(s => ({
      name: s.name,
      type: 'bar',
      stack: 'total',
      data: s.data
    }))
  }
})

// 风险与性别关系图
const riskGenderOption = computed(() => {
  const data = staticRiskAnalysisData.risk_by_gender || { categories: [], series: [] }
  
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: data.series?.map(s => s.name) || [] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.categories || []
    },
    yAxis: { type: 'value' },
    series: (data.series || []).map(s => ({
      name: s.name,
      type: 'bar',
      data: s.data
    }))
  }
})

// 相关性热力图配置
const correlationOption = computed(() => {
  const categories = staticCorrelationData.categories || []
  const data = staticCorrelationData.data || []
  
  return {
    tooltip: {
      position: 'top',
      formatter: function (params) {
        return `${categories[params.value[0]]} vs ${categories[params.value[1]]}<br/>相关性: ${params.value[2]}`
      }
    },
    grid: { height: '70%', top: '10%' },
    xAxis: {
      type: 'category',
      data: categories,
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: categories,
      splitArea: { show: true }
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
      }
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: { show: true },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
})
</script>

<style lang="scss" scoped>
.analysis-container {
  .mt-20 {
    margin-top: 20px;
  }
}
</style>
