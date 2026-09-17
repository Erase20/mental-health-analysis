<template>
  <div class="self-assessment-container">
    <el-row :gutter="20">
      <!-- 左侧：填写表单 -->
      <el-col :xs="24" :lg="12">
        <div class="dashboard-card">
          <div class="card-header">
            <span class="title">心理健康自评</span>
            <el-button type="primary" :loading="submitting" @click="handleSubmit">
              <el-icon><Check /></el-icon>
              提交评估
            </el-button>
          </div>
          <el-form
            ref="formRef"
            :model="form"
            :rules="formRules"
            label-width="120px"
            class="assessment-form"
          >
            <!-- 基本信息 -->
            <el-divider content-position="left">基本信息</el-divider>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="年龄" prop="age">
                  <el-input-number v-model="form.age" :min="18" :max="100" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="性别" prop="gender">
                  <el-select v-model="form.gender" placeholder="请选择">
                    <el-option label="男" value="Male" />
                    <el-option label="女" value="Female" />
                    <el-option label="非二元" value="Non-binary" />
                    <el-option label="不愿透露" value="Prefer not to say" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="是否自雇" prop="self_employed">
                  <el-select v-model="form.self_employed" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="公司人数" prop="no_employees">
                  <el-select v-model="form.no_employees" placeholder="请选择">
                    <el-option label="1-5人" value="1-5" />
                    <el-option label="6-25人" value="6-25" />
                    <el-option label="26-100人" value="26-100" />
                    <el-option label="100-500人" value="100-500" />
                    <el-option label="500-1000人" value="500-1000" />
                    <el-option label="1000人以上" value="More than 1000" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 健康与工作 -->
            <el-divider content-position="left">健康与工作</el-divider>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="家族病史" prop="family_history">
                  <el-select v-model="form.family_history" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="是否治疗" prop="treatment">
                  <el-select v-model="form.treatment" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="工作干扰" prop="work_interfere">
                  <el-select v-model="form.work_interfere" placeholder="请选择">
                    <el-option label="经常" value="Often" />
                    <el-option label="有时" value="Sometimes" />
                    <el-option label="很少" value="Rarely" />
                    <el-option label="从不" value="Never" />
                    <el-option label="不适用" value="Not applicable" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="远程工作" prop="remote_work">
                  <el-select v-model="form.remote_work" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="科技公司" prop="tech_company">
                  <el-select v-model="form.tech_company" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="负面后果" prop="obs_consequence">
                  <el-select v-model="form.obs_consequence" placeholder="是否观察到负面后果">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 公司福利 -->
            <el-divider content-position="left">公司福利与支持</el-divider>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="心理健康福利" prop="benefits">
                  <el-select v-model="form.benefits" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                    <el-option label="不知道" value="Don't know" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="护理选项" prop="care_options">
                  <el-select v-model="form.care_options" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                    <el-option label="不确定" value="Not sure" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="健康项目" prop="wellness_program">
                  <el-select v-model="form.wellness_program" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                    <el-option label="不知道" value="Don't know" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="寻求帮助" prop="seek_help">
                  <el-select v-model="form.seek_help" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                    <el-option label="不知道" value="Don't know" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="匿名保护" prop="anonymity">
                  <el-select v-model="form.anonymity" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                    <el-option label="不知道" value="Don't know" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="请假难度" prop="leave">
                  <el-select v-model="form.leave" placeholder="请选择">
                    <el-option label="非常困难" value="Very difficult" />
                    <el-option label="有些困难" value="Somewhat difficult" />
                    <el-option label="有些容易" value="Somewhat easy" />
                    <el-option label="非常容易" value="Very easy" />
                    <el-option label="不知道" value="Don't know" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 心理健康态度 -->
            <el-divider content-position="left">心理健康态度</el-divider>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="心理后果" prop="mental_health_consequence">
                  <el-select v-model="form.mental_health_consequence" placeholder="讨论心理健康的后果">
                    <el-option label="是" value="Yes" />
                    <el-option label="也许" value="Maybe" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="身体后果" prop="phys_health_consequence">
                  <el-select v-model="form.phys_health_consequence" placeholder="讨论身体健康的后果">
                    <el-option label="是" value="Yes" />
                    <el-option label="也许" value="Maybe" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="同事态度" prop="coworkers">
                  <el-select v-model="form.coworkers" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="部分同事" value="Some of them" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="上级态度" prop="supervisor">
                  <el-select v-model="form.supervisor" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="部分上级" value="Some of them" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="面试提及" prop="mental_health_interview">
                  <el-select v-model="form.mental_health_interview" placeholder="面试时是否会提及心理健康">
                    <el-option label="是" value="Yes" />
                    <el-option label="也许" value="Maybe" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="身心同等" prop="mental_vs_physical">
                  <el-select v-model="form.mental_vs_physical" placeholder="心理健康与身体健康同等重要">
                    <el-option label="是" value="Yes" />
                    <el-option label="不知道" value="Don't know" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-col>

      <!-- 右侧：评估结果 -->
      <el-col :xs="24" :lg="12">
        <!-- 未评估提示 -->
        <div v-if="!result" class="dashboard-card empty-result">
          <el-empty description="请填写左侧表单后提交评估，查看您的心理健康画像和风险等级" />
        </div>

        <!-- 评估结果 -->
        <template v-else>
          <!-- 风险概况 -->
          <div class="dashboard-card">
            <div class="card-header">
              <span class="title">风险概况</span>
            </div>
            <div class="risk-overview">
              <div class="risk-score-wrap">
                <el-progress
                  type="dashboard"
                  :percentage="result.risk_score"
                  :color="progressColors"
                  :stroke-width="10"
                  :width="160"
                />
                <div class="score-label">风险评分</div>
              </div>
              <div class="risk-info">
                <div class="risk-level-item">
                  <span class="label">风险等级:</span>
                  <el-tag :type="getRiskTagType(result.risk_level)" size="large" effect="dark">
                    {{ riskLevelLabel(result.risk_level) }}
                  </el-tag>
                </div>
                <div v-if="result.prediction" class="risk-level-item">
                  <span class="label">模型预测:</span>
                  <el-tag :type="getRiskTagType(result.prediction)" size="large">
                    {{ riskLevelLabel(result.prediction) }}
                  </el-tag>
                </div>
                <p class="description">{{ result.description }}</p>
              </div>
            </div>
          </div>

          <!-- 概率分布 -->
          <div v-if="result.probabilities" class="dashboard-card mt-20">
            <div class="card-header">
              <span class="title">风险概率分布</span>
            </div>
            <div class="probability-section">
              <div v-for="(prob, label) in result.probabilities" :key="label" class="prob-bar">
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

          <!-- 画像标签 -->
          <div class="dashboard-card mt-20">
            <div class="card-header">
              <span class="title">画像标签</span>
            </div>
            <div class="tags-section">
              <el-tag
                v-for="tag in result.tags"
                :key="tag"
                size="large"
                effect="dark"
                style="margin: 5px"
              >
                {{ tag }}
              </el-tag>
              <el-empty v-if="!result.tags || result.tags.length === 0" description="暂无标签" :image-size="60" />
            </div>
          </div>

          <!-- 关键特征 -->
          <div class="dashboard-card mt-20">
            <div class="card-header">
              <span class="title">关键特征</span>
            </div>
            <el-descriptions :column="2" border>
              <el-descriptions-item
                v-for="(value, key) in result.key_features"
                :key="key"
                :label="key"
              >
                <span v-if="value === 'Yes'" style="color: #f56c6c; font-weight: 600">是</span>
                <span v-else-if="value === 'No'" style="color: #67c23a">否</span>
                <span v-else>{{ value }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 健康建议 -->
          <div class="dashboard-card mt-20">
            <div class="card-header">
              <span class="title">健康建议</span>
            </div>
            <el-timeline>
              <el-timeline-item
                v-for="(rec, index) in result.recommendations"
                :key="index"
                :type="index === 0 ? 'primary' : 'info'"
                :hollow="index > 0"
              >
                {{ rec }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { submitSelfAssessment } from '@/api/user'

const formRef = ref(null)
const submitting = ref(false)
const result = ref(null)

const form = reactive({
  age: 30,
  gender: '',
  self_employed: '',
  no_employees: '',
  family_history: '',
  treatment: '',
  work_interfere: '',
  remote_work: '',
  tech_company: '',
  obs_consequence: '',
  benefits: '',
  care_options: '',
  wellness_program: '',
  seek_help: '',
  anonymity: '',
  leave: '',
  mental_health_consequence: '',
  phys_health_consequence: '',
  coworkers: '',
  supervisor: '',
  mental_health_interview: '',
  mental_vs_physical: ''
})

const formRules = {
  age: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  family_history: [{ required: true, message: '请选择', trigger: 'change' }],
  treatment: [{ required: true, message: '请选择', trigger: 'change' }],
  work_interfere: [{ required: true, message: '请选择', trigger: 'change' }]
}

const progressColors = [
  { color: '#67c23a', percentage: 40 },
  { color: '#e6a23c', percentage: 70 },
  { color: '#f56c6c', percentage: 100 }
]

const getRiskTagType = (risk) => {
  const types = {
    'Low Risk': 'success',
    'Medium Risk': 'warning',
    'High Risk': 'danger'
  }
  return types[risk] || 'info'
}

const riskLevelLabel = (level) => {
  const labels = {
    'Low Risk': '低风险',
    'Medium Risk': '中风险',
    'High Risk': '高风险'
  }
  return labels[level] || level
}

const getProgressColor = (label) => {
  const colors = {
    'Low Risk': '#67c23a',
    'Medium Risk': '#e6a23c',
    'High Risk': '#f56c6c'
  }
  return colors[label] || '#409eff'
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请填写必填项')
      return
    }
    submitting.value = true
    try {
      const res = await submitSelfAssessment({ ...form })
      if (res.code === 200) {
        result.value = res.data
        // 保存到 localStorage 供「我的分析」页面读取
        localStorage.setItem('last_assessment_result', JSON.stringify(res.data))
        ElMessage.success('评估完成')
      }
    } catch (error) {
      ElMessage.error(error.message || '评估失败')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style lang="scss" scoped>
.self-assessment-container {
  .mt-20 {
    margin-top: 20px;
  }

  .assessment-form {
    margin-top: 10px;
    max-height: calc(100vh - 220px);
    overflow-y: auto;
    padding-right: 10px;
  }

  .empty-result {
    min-height: 400px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .risk-overview {
    display: flex;
    align-items: center;
    gap: 30px;
    padding: 10px 0;

    .risk-score-wrap {
      text-align: center;
      flex-shrink: 0;

      .score-label {
        margin-top: 10px;
        font-size: 16px;
        color: #606266;
      }
    }

    .risk-info {
      flex: 1;

      .risk-level-item {
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;

        .label {
          color: #909399;
          font-size: 14px;
          white-space: nowrap;
        }
      }

      .description {
        margin-top: 12px;
        color: #606266;
        font-size: 14px;
        line-height: 1.6;
      }
    }
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

  .tags-section {
    min-height: 40px;
  }
}
</style>
