<template>
  <div class="analysis-container" v-loading="loading">
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
              <v-chart
                v-if="hasData(currentFeatureData)"
                class="chart-container"
                :option="featurePieOption"
                autoresize
              />
              <el-empty v-else class="chart-empty" description="暂无特征数据" />
            </el-col>
            <el-col :xs="24" :lg="12">
              <v-chart
                v-if="hasData(currentFeatureData)"
                class="chart-container"
                :option="featureBarOption"
                autoresize
              />
              <el-empty v-else class="chart-empty" description="暂无特征数据" />
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
          <v-chart
            v-if="hasData(riskAnalysisData.risk_by_age)"
            class="chart-container"
            :option="riskAgeOption"
            autoresize
          />
          <el-empty v-else class="chart-empty" description="暂无风险与年龄数据" />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">风险等级与性别关系</span>
          </div>
          <v-chart
            v-if="hasData(riskAnalysisData.risk_by_gender)"
            class="chart-container"
            :option="riskGenderOption"
            autoresize
          />
          <el-empty v-else class="chart-empty" description="暂无风险与性别数据" />
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
          <v-chart
            v-if="hasData(correlationData)"
            class="chart-container"
            :option="correlationOption"
            autoresize
          />
          <el-empty v-else class="chart-empty" description="暂无可计算的相关性数据" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
import { getCorrelation, getFeatureAnalysis, getRiskAnalysis } from '@/api/visualization'

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
const loading = ref(false)
const featureData = ref({})
const riskAnalysisData = ref({
  risk_by_age: { categories: [], series: [] },
  risk_by_gender: { categories: [], series: [] }
})
const correlationData = ref({ categories: [], data: [] })

const RISK_LABELS = {
  'Low Risk': '低风险',
  'Medium Risk': '中风险',
  'High Risk': '高风险'
}

// 后端保存英文值是为了稳定计算；前端在展示层统一翻译成中文。
const VALUE_LABELS = {
  Yes: '是',
  No: '否',
  "Don't know": '不知道',
  'Not sure': '不确定',
  Never: '从不',
  Rarely: '很少',
  Sometimes: '有时',
  Often: '经常'
}

const CORRELATION_LABELS = {
  age: '年龄',
  cluster_id: '聚类群体',
  risk_level_encoded: '风险等级',
  gender_encoded: '性别',
  treatment_encoded: '治疗情况'
}

const currentFeatureData = computed(() => {
  const key = `${selectedFeature.value}_distribution`
  return featureData.value[key] || {}
})

const hasData = (data) => {
  // 不同接口的数据格式不同：分布是对象，风险图是 series，相关性是 data。
  if (!data) return false
  if (Array.isArray(data)) return data.length > 0
  if (Array.isArray(data.series)) return data.series.length > 0
  if (Array.isArray(data.data)) return data.data.length > 0
  return Object.values(data).some(value => Number(value) > 0)
}

const translateValue = (value) => VALUE_LABELS[value] || value

// 特征饼图配置
const featurePieOption = computed(() => {
  const data = currentFeatureData.value
  
  return {
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: '60%',
      data: Object.entries(data).map(([name, value]) => ({
        name: translateValue(name),
        value
      })),
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
  const data = currentFeatureData.value
  const categories = Object.keys(data).map(translateValue)
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
  const data = riskAnalysisData.value.risk_by_age || { categories: [], series: [] }
  
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: data.series?.map(s => RISK_LABELS[s.name] || s.name) || [] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.categories || []
    },
    yAxis: { type: 'value' },
    series: (data.series || []).map(s => ({
      name: RISK_LABELS[s.name] || s.name,
      type: 'bar',
      stack: 'total',
      data: s.data
    }))
  }
})

// 风险与性别关系图
const riskGenderOption = computed(() => {
  const data = riskAnalysisData.value.risk_by_gender || { categories: [], series: [] }
  
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: data.series?.map(s => RISK_LABELS[s.name] || s.name) || [] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.categories || []
    },
    yAxis: { type: 'value' },
    series: (data.series || []).map(s => ({
      name: RISK_LABELS[s.name] || s.name,
      type: 'bar',
      data: s.data
    }))
  }
})

// 相关性热力图配置
const correlationOption = computed(() => {
  const categories = (correlationData.value.categories || []).map(
    name => CORRELATION_LABELS[name] || name
  )
  const data = correlationData.value.data || []
  
  return {
    tooltip: {
      position: 'top',
      formatter: function (params) {
        return `${categories[params.value[0]]} 与 ${categories[params.value[1]]}<br/>相关系数：${params.value[2]}`
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

const fetchData = async () => {
  loading.value = true
  try {
    // 三个接口互不依赖，使用 Promise.all 并行请求以减少首屏等待时间。
    const [featureRes, riskRes, correlationRes] = await Promise.all([
      getFeatureAnalysis(),
      getRiskAnalysis(),
      getCorrelation()
    ])

    if (featureRes.code === 200) featureData.value = featureRes.data || {}
    if (riskRes.code === 200) {
      riskAnalysisData.value = {
        risk_by_age: riskRes.data?.risk_by_age || { categories: [], series: [] },
        risk_by_gender: riskRes.data?.risk_by_gender || { categories: [], series: [] }
      }
    }
    if (correlationRes.code === 200) correlationData.value = correlationRes.data || {}
  } catch (error) {
    console.error('获取分析数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style lang="scss" scoped>
.analysis-container {
  .mt-20 {
    margin-top: 20px;
  }

  .chart-empty {
    height: 320px;
    display: flex;
    justify-content: center;
  }
}
</style>
