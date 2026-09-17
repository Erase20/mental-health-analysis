<template>
  <div class="classification-container">
    <!-- 操作栏 -->
    <div class="dashboard-card">
      <div class="card-header">
        <span class="title">分类预测模型</span>
        <el-button type="primary" :loading="loading" @click="runClassification">
          <el-icon><Refresh /></el-icon>
          训练模型
        </el-button>
      </div>
      <el-alert
        v-if="classificationResult"
        :title="`模型训练完成！准确率: ${((classificationResult.metrics?.accuracy || classificationResult.accuracy) * 100).toFixed(2)}%, F1分数: ${((classificationResult.metrics?.f1_score || classificationResult.f1_score) * 100).toFixed(2)}%`"
        type="success"
        :closable="false"
        show-icon
      />
    </div>
    
    <!-- 模型性能指标 -->
    <el-row :gutter="20" v-if="classificationResult">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-card-success">
          <div class="stat-title">准确率 (Accuracy)</div>
          <div class="stat-value">{{ ((classificationResult.metrics?.accuracy || classificationResult.accuracy) * 100).toFixed(2) }}%</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-card-info">
          <div class="stat-title">精确率 (Precision)</div>
          <div class="stat-value">{{ ((classificationResult.metrics?.precision || classificationResult.precision) * 100).toFixed(2) }}%</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-card-warning">
          <div class="stat-title">召回率 (Recall)</div>
          <div class="stat-value">{{ ((classificationResult.metrics?.recall || classificationResult.recall) * 100).toFixed(2) }}%</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-title">F1分数</div>
          <div class="stat-value">{{ ((classificationResult.metrics?.f1_score || classificationResult.f1_score) * 100).toFixed(2) }}%</div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 特征重要性 -->
    <el-row :gutter="20" v-if="classificationResult" class="mt-20">
      <el-col :xs="24">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">特征重要性</span>
          </div>
          <v-chart class="chart-container" :option="featureImportanceOption" autoresize />
        </div>
      </el-col>
    </el-row>
    
    <!-- 风险预测 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">风险等级预测</span>
          </div>
          <el-form :model="predictForm" label-width="120px" class="predict-form">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8">
                <el-form-item label="年龄">
                  <el-input-number v-model="predictForm.age" :min="18" :max="100" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8">
                <el-form-item label="压力指数">
                  <el-slider v-model="predictForm.stress_index" :max="1" :step="0.1" show-stops />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8">
                <el-form-item label="支持度评分">
                  <el-slider v-model="predictForm.support_score" :max="1" :step="0.1" show-stops />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8">
                <el-form-item label="公司规模">
                  <el-select v-model="predictForm.company_size_encoded" placeholder="选择公司规模">
                    <el-option label="小型 (1-5人)" :value="0" />
                    <el-option label="中小型 (6-25人)" :value="1" />
                    <el-option label="中型 (26-100人)" :value="2" />
                    <el-option label="大型 (100-500人)" :value="3" />
                    <el-option label="超大型 (500+人)" :value="4" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8">
                <el-form-item label="态度评分">
                  <el-slider v-model="predictForm.attitude_score" :max="1" :step="0.1" show-stops />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8">
                <el-form-item label="家族治疗史">
                  <el-switch
                    v-model="predictForm.family_treatment_interaction"
                    :active-value="1"
                    :inactive-value="0"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item>
              <el-button type="primary" :loading="predictLoading" @click="handlePredict">
                预测风险等级
              </el-button>
            </el-form-item>
          </el-form>
          
          <!-- 预测结果 -->
          <div v-if="predictResult" class="predict-result">
            <el-divider />
            <h4>预测结果</h4>
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12">
                <div class="result-item">
                  <span class="label">预测风险等级:</span>
                  <el-tag :type="getRiskTagType(predictResult.prediction)" size="large">
                    {{ predictResult.prediction }}
                  </el-tag>
                </div>
              </el-col>
              <el-col :xs="24" :sm="12">
                <div class="result-item">
                  <span class="label">概率分布:</span>
                  <div class="probability-bars">
                    <div v-for="(prob, label) in predictResult.probabilities" :key="label" class="prob-bar">
                      <span class="prob-label">{{ label }}:</span>
                      <el-progress :percentage="Math.round(prob * 100)" :color="getProgressColor(label)" />
                    </div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent
} from 'echarts/components'
import { ElMessage } from 'element-plus'
import { runClassification as apiRunClassification, predictRisk } from '@/api/analysis'
import { getLatestAnalysis } from '@/api/analysis'

use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  GridComponent
])

const loading = ref(false)
const predictLoading = ref(false)
const classificationResult = ref(null)
const predictResult = ref(null)

const predictForm = ref({
  age: 30,
  stress_index: 0.5,
  support_score: 0.5,
  company_size_encoded: 2,
  attitude_score: 0.5,
  family_treatment_interaction: 0,
  remote_tech_interaction: 0,
  has_observed_consequence: 0
})

// 特征重要性配置
const featureImportanceOption = computed(() => {
  const importance = classificationResult.value?.feature_importance || {}
  const sortedFeatures = Object.entries(importance)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
  
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', max: 1 },
    yAxis: {
      type: 'category',
      data: sortedFeatures.map(f => f[0]).reverse()
    },
    series: [{
      type: 'bar',
      data: sortedFeatures.map(f => f[1]).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      barWidth: '60%'
    }]
  }
})

const getRiskTagType = (risk) => {
  const types = {
    'Low Risk': 'success',
    'Medium Risk': 'warning',
    'High Risk': 'danger'
  }
  return types[risk] || 'info'
}

const getProgressColor = (label) => {
  const colors = {
    'Low Risk': '#67c23a',
    'Medium Risk': '#e6a23c',
    'High Risk': '#f56c6c'
  }
  return colors[label] || '#409eff'
}

const runClassification = async () => {
  loading.value = true
  try {
    const res = await apiRunClassification()
    if (res.code === 200) {
      classificationResult.value = res.data
      ElMessage.success('模型训练完成')
    }
  } catch (error) {
    ElMessage.error(error.message || '模型训练失败')
  } finally {
    loading.value = false
  }
}

const handlePredict = async () => {
  predictLoading.value = true
  try {
    const res = await predictRisk(predictForm.value)
    if (res.code === 200) {
      predictResult.value = res.data
      ElMessage.success('预测完成')
    }
  } catch (error) {
    ElMessage.error(error.message || '预测失败')
  } finally {
    predictLoading.value = false
  }
}

const fetchLatestResult = async () => {
  try {
    const res = await getLatestAnalysis('classification')
    if (res.code === 200 && res.data) {
      classificationResult.value = res.data
    }
  } catch (error) {
    console.error('获取最新分析结果失败:', error)
  }
}

onMounted(() => {
  fetchLatestResult()
})
</script>

<style lang="scss" scoped>
.classification-container {
  .mt-20 {
    margin-top: 20px;
  }
  
  .predict-form {
    margin-top: 20px;
  }
  
  .predict-result {
    margin-top: 20px;
    
    .result-item {
      display: flex;
      flex-direction: column;
      gap: 10px;
      
      .label {
        font-weight: 600;
        color: #606266;
      }
      
      .probability-bars {
        .prob-bar {
          display: flex;
          align-items: center;
          margin-bottom: 10px;
          
          .prob-label {
            width: 100px;
            font-size: 14px;
          }
          
          .el-progress {
            flex: 1;
          }
        }
      }
    }
  }
}
</style>
