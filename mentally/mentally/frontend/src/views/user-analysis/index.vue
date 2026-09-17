<template>
  <div class="user-analysis-container">
    <!-- 最新评估结果 -->
    <div class="dashboard-card">
      <div class="card-header">
        <span class="title">我的分析结果</span>
        <el-button type="primary" @click="$router.push('/self-assessment')">
          <el-icon><FirstAidKit /></el-icon>
          去自评
        </el-button>
      </div>

      <el-empty v-if="!latestResult" description="暂无分析结果，请先完成心理自评">
        <el-button type="primary" @click="$router.push('/self-assessment')">立即自评</el-button>
      </el-empty>

      <template v-else>
        <!-- 风险概况 -->
        <el-row :gutter="20">
          <el-col :xs="24" :sm="8">
            <div class="stat-card" :class="getRiskCardClass(latestResult.risk_level)">
              <div class="stat-title">风险等级</div>
              <div class="stat-value">{{ riskLevelLabel(latestResult.risk_level) }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div class="stat-card">
              <div class="stat-title">风险评分</div>
              <div class="stat-value">{{ latestResult.risk_score }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div class="stat-card stat-card-info">
              <div class="stat-title">画像标签数</div>
              <div class="stat-value">{{ latestResult.tags?.length || 0 }}</div>
            </div>
          </el-col>
        </el-row>

        <!-- 详细分析 -->
        <el-row :gutter="20" class="mt-20">
          <el-col :xs="24" :lg="12">
            <div class="dashboard-card">
              <div class="card-header">
                <span class="title">画像标签</span>
              </div>
              <div class="tags-section">
                <el-tag
                  v-for="tag in latestResult.tags"
                  :key="tag"
                  size="large"
                  effect="dark"
                  style="margin: 5px"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :lg="12">
            <div class="dashboard-card">
              <div class="card-header">
                <span class="title">关键特征</span>
              </div>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item
                  v-for="(value, key) in latestResult.key_features"
                  :key="key"
                  :label="key"
                >
                  {{ value }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>
        </el-row>

        <!-- 概率分布 -->
        <div v-if="latestResult.probabilities" class="dashboard-card mt-20">
          <div class="card-header">
            <span class="title">风险概率分布</span>
          </div>
          <div class="probability-section">
            <div v-for="(prob, label) in latestResult.probabilities" :key="label" class="prob-bar">
              <span class="prob-label">{{ riskLevelLabel(label) }}</span>
              <el-progress
                :percentage="Math.round(prob * 100)"
                :color="getProgressColor(label)"
                :stroke-width="18"
                :text-inside="true"
              />
            </div>
          </div>
        </div>

        <!-- 健康建议 -->
        <div class="dashboard-card mt-20">
          <div class="card-header">
            <span class="title">健康建议</span>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="(rec, index) in latestResult.recommendations"
              :key="index"
              :type="index === 0 ? 'primary' : 'info'"
              :hollow="index > 0"
            >
              {{ rec }}
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 描述 -->
        <div class="dashboard-card mt-20">
          <div class="card-header">
            <span class="title">综合评价</span>
          </div>
          <p class="description-text">{{ latestResult.description }}</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const latestResult = ref(null)

const riskLevelLabel = (level) => {
  const labels = {
    'Low Risk': '低风险',
    'Medium Risk': '中风险',
    'High Risk': '高风险'
  }
  return labels[level] || level
}

const getRiskCardClass = (risk) => {
  const classes = {
    'Low Risk': 'stat-card-success',
    'Medium Risk': 'stat-card-warning',
    'High Risk': 'stat-card-danger'
  }
  return classes[risk] || ''
}

const getProgressColor = (label) => {
  const colors = {
    'Low Risk': '#67c23a',
    'Medium Risk': '#e6a23c',
    'High Risk': '#f56c6c'
  }
  return colors[label] || '#409eff'
}

onMounted(() => {
  // 从 localStorage 中读取上次自评结果
  const saved = localStorage.getItem('last_assessment_result')
  if (saved) {
    try {
      latestResult.value = JSON.parse(saved)
    } catch (e) {
      console.error('解析自评结果失败:', e)
    }
  }
})
</script>

<style lang="scss" scoped>
.user-analysis-container {
  .mt-20 {
    margin-top: 20px;
  }

  .tags-section {
    min-height: 40px;
  }

  .probability-section {
    .prob-bar {
      display: flex;
      align-items: center;
      margin-bottom: 16px;

      .prob-label {
        width: 70px;
        font-size: 14px;
        color: #606266;
        flex-shrink: 0;
      }

      .el-progress {
        flex: 1;
      }
    }
  }

  .description-text {
    color: #606266;
    font-size: 14px;
    line-height: 1.8;
    padding: 10px 0;
  }

  .stat-card-danger {
    background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%) !important;
    .stat-title, .stat-value {
      color: #fff !important;
    }
  }

  .stat-card-info {
    background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%) !important;
    .stat-title, .stat-value {
      color: #fff !important;
    }
  }
}
</style>
