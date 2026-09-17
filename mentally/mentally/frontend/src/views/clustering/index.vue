<template>
  <div class="clustering-container">
    <!-- 操作栏 -->
    <div class="dashboard-card">
      <div class="card-header">
        <span class="title">聚类分析</span>
        <el-tag type="success">K=3 | 轮廓系数: 0.2040</el-tag>
      </div>
      <el-alert
        title="聚类完成！最优K值: 3, 轮廓系数: 0.2040"
        type="success"
        :closable="false"
        show-icon
      />
    </div>

    <!-- 聚类结果 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">聚类分布</span>
          </div>
          <v-chart class="chart-container" :option="clusterPieOption" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">轮廓系数对比</span>
          </div>
          <v-chart class="chart-container" :option="silhouetteOption" autoresize />
        </div>
      </el-col>
    </el-row>

    <!-- 群体特征 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">群体特征对比</span>
          </div>
          <el-table :data="clusterTableData" border stripe>
            <el-table-column prop="name" label="群体名称" width="120" />
            <el-table-column prop="size" label="规模" width="100" />
            <el-table-column prop="avg_age" label="平均年龄" width="100" />
            <el-table-column prop="treatment_rate" label="治疗率" width="100">
              <template #default="{ row }">
                <el-progress :percentage="row.treatment_rate" :color="progressColors" />
              </template>
            </el-table-column>
            <el-table-column prop="remote_work_rate" label="远程工作率" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.remote_work_rate" :color="progressColors" />
              </template>
            </el-table-column>
            <el-table-column prop="tech_company_rate" label="科技公司占比" width="130">
              <template #default="{ row }">
                <el-progress :percentage="row.tech_company_rate" :color="progressColors" />
              </template>
            </el-table-column>
            <el-table-column prop="top_country" label="主要国家" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <!-- 雷达图对比 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :xs="24" :sm="12" :lg="6" v-for="id in clusterIds" :key="id">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">{{ getClusterName(id) }}</span>
          </div>
          <v-chart class="chart-container" :option="getRadarOption(id)" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, RadarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  PieChart,
  BarChart,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent
])

const progressColors = [
  { color: '#f56c6c', percentage: 30 },
  { color: '#e6a23c', percentage: 60 },
  { color: '#67c23a', percentage: 100 }
]

const clusterIds = [0, 1, 2, 3]

const getClusterName = (id) => {
  const names = { 0: '高风险群体', 1: '中高风险群体', 2: '中风险群体', 3: '低风险群体', 4: '超低风险群体' }
  return names[id] || `群体_${id}`
}

const clusterTableData = [
  {
    name: '高风险群体',
    size: 856,
    avg_age: 32.5,
    treatment_rate: 48.2,
    remote_work_rate: 28.6,
    tech_company_rate: 72.3,
    top_country: 'United States'
  },
  {
    name: '中高风险群体',
    size: 723,
    avg_age: 28.3,
    treatment_rate: 65.7,
    remote_work_rate: 45.2,
    tech_company_rate: 85.1,
    top_country: 'United States'
  },
  {
    name: '中风险群体',
    size: 421,
    avg_age: 38.7,
    treatment_rate: 75.4,
    remote_work_rate: 55.8,
    tech_company_rate: 68.9,
    top_country: 'United Kingdom'
  },
  {
    name: '低风险群体',
    size: 285,
    avg_age: 35.2,
    treatment_rate: 82.5,
    remote_work_rate: 55.3,
    tech_company_rate: 68.7,
    top_country: 'United States'
  }
]

const clusterPieOption = {
  tooltip: { trigger: 'item' },
  legend: { bottom: '5%' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    avoidLabelOverlap: false,
    itemStyle: {
      borderRadius: 10,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: {
      show: true,
      formatter: '{b}: {c} ({d}%)'
    },
    data: [
      { name: '高风险群体', value: 856 },
      { name: '中高风险群体', value: 723 },
      { name: '中风险群体', value: 421 },
      { name: '低风险群体', value: 285 }
    ]
  }]
}

const silhouetteOption = {
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['K=2', 'K=3', 'K=4']
  },
  yAxis: {
    type: 'value',
    max: 1,
    min: 0
  },
  series: [{
    data: [
      { value: 0.1823, itemStyle: { color: '#409eff' } },
      { value: 0.2040, itemStyle: { color: '#67c23a' } },
      { value: 0.1891, itemStyle: { color: '#409eff' } }
    ],
    type: 'bar',
    markPoint: {
      data: [
        { type: 'max', name: '最大值' }
      ]
    }
  }]
}

const radarData = {
  0: [72.5, 65.3, 48.2, 28.6, 58.4],
  1: [85.2, 78.6, 65.7, 45.2, 72.1],
  2: [88.3, 82.1, 75.4, 55.8, 65.6],
  3: [92.5, 88.6, 82.5, 65.3, 78.4]
}

const radarColors = {
  0: '#f56c6c',
  1: '#e6a23c',
  2: '#409eff',
  3: '#67c23a'
}

const getRadarOption = (id) => {
  return {
    tooltip: {},
    radar: {
      indicator: [
        { name: '工作支持度', max: 100 },
        { name: '心理健康意识', max: 100 },
        { name: '治疗意愿', max: 100 },
        { name: '工作灵活性', max: 100 },
        { name: '社会支持', max: 100 }
      ],
      radius: '65%'
    },
    series: [{
      type: 'radar',
      data: [{
        value: radarData[id],
        name: getClusterName(id),
        areaStyle: {
          color: `rgba(${hexToRgb(radarColors[id])}, 0.3)`
        },
        lineStyle: {
          color: radarColors[id]
        }
      }]
    }]
  }
}

const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
    : '64, 158, 255'
}
</script>

<style lang="scss" scoped>
.clustering-container {
  .mt-20 {
    margin-top: 20px;
  }
}
</style>
