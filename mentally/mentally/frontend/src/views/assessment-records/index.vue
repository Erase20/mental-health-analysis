<template>
  <div class="assessment-records-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-title">总评估数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-danger">
          <div class="stat-title">高风险</div>
          <div class="stat-value">{{ stats.high_risk }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-warning">
          <div class="stat-title">中风险</div>
          <div class="stat-value">{{ stats.medium_risk }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-success">
          <div class="stat-title">低风险</div>
          <div class="stat-value">{{ stats.low_risk }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选和表格 -->
    <div class="dashboard-card">
      <div class="card-header">
        <span class="title">自评记录列表</span>
        <div class="filter-area">
          <el-input
            v-model="filter.username"
            placeholder="搜索用户名"
            clearable
            style="width: 150px; margin-right: 10px"
            @clear="fetchRecords"
            @keyup.enter="fetchRecords"
          />
          <el-select v-model="filter.risk_level" placeholder="风险等级" clearable style="width: 130px; margin-right: 10px" @change="fetchRecords">
            <el-option label="高风险" value="High Risk" />
            <el-option label="中风险" value="Medium Risk" />
            <el-option label="低风险" value="Low Risk" />
          </el-select>
          <el-button type="primary" @click="fetchRecords">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
        </div>
      </div>

      <el-table :data="records" border stripe v-loading="loading" empty-text="暂无自评记录">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="age" label="年龄" width="70" />
        <el-table-column prop="gender" label="性别" width="80">
          <template #default="{ row }">
            {{ genderLabel(row.gender) }}
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="120">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" effect="dark">
              {{ riskLevelLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_score" label="风险评分" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="row.risk_score"
              :color="getScoreColor(row.risk_score)"
              :stroke-width="10"
              :show-text="true"
              style="width: 80px"
            />
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" min-width="180">
          <template #default="{ row }">
            <el-tag v-for="tag in (row.tags || []).slice(0, 3)" :key="tag" size="small" style="margin: 2px">
              {{ tag }}
            </el-tag>
            <span v-if="(row.tags || []).length > 3" class="more-tag">+{{ row.tags.length - 3 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="评估时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="showDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchRecords"
          @size-change="fetchRecords"
        />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="自评详情" width="700px" destroy-on-close>
      <template v-if="currentRecord">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="用户">{{ currentRecord.username }}</el-descriptions-item>
          <el-descriptions-item label="评估时间">{{ currentRecord.created_at }}</el-descriptions-item>
          <el-descriptions-item label="年龄">{{ currentRecord.age }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ genderLabel(currentRecord.gender) }}</el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag :type="riskTagType(currentRecord.risk_level)" effect="dark">
              {{ riskLevelLabel(currentRecord.risk_level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风险评分">{{ currentRecord.risk_score }}</el-descriptions-item>
          <el-descriptions-item label="家族病史">{{ currentRecord.family_history }}</el-descriptions-item>
          <el-descriptions-item label="是否治疗">{{ currentRecord.treatment }}</el-descriptions-item>
          <el-descriptions-item label="工作干扰">{{ currentRecord.work_interfere }}</el-descriptions-item>
          <el-descriptions-item label="远程工作">{{ currentRecord.remote_work }}</el-descriptions-item>
          <el-descriptions-item label="科技公司">{{ currentRecord.tech_company }}</el-descriptions-item>
          <el-descriptions-item label="公司福利">{{ currentRecord.benefits }}</el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">画像标签</el-divider>
        <div>
          <el-tag v-for="tag in currentRecord.tags" :key="tag" style="margin: 4px" effect="dark">
            {{ tag }}
          </el-tag>
        </div>

        <el-divider content-position="left">关键特征</el-divider>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item v-for="(val, key) in currentRecord.key_features" :key="key" :label="key">
            {{ val }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">概率分布</el-divider>
        <div v-if="currentRecord.probabilities" class="probability-section">
          <div v-for="(prob, label) in currentRecord.probabilities" :key="label" class="prob-bar">
            <span class="prob-label">{{ riskLevelLabel(label) }}</span>
            <el-progress
              :percentage="Math.round(prob * 100)"
              :color="getProgressColor(label)"
              :stroke-width="16"
              :text-inside="true"
            />
          </div>
        </div>

        <el-divider content-position="left">健康建议</el-divider>
        <el-timeline>
          <el-timeline-item v-for="(rec, idx) in currentRecord.recommendations" :key="idx" :type="idx === 0 ? 'primary' : 'info'">
            {{ rec }}
          </el-timeline-item>
        </el-timeline>

        <el-divider content-position="left">综合评价</el-divider>
        <p>{{ currentRecord.description }}</p>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAssessmentRecords, getAssessmentStats } from '@/api/user'

const loading = ref(false)
const records = ref([])
const detailVisible = ref(false)
const currentRecord = ref(null)

const stats = ref({ total: 0, high_risk: 0, medium_risk: 0, low_risk: 0 })

const filter = reactive({
  username: '',
  risk_level: ''
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const genderLabel = (g) => {
  const map = { 'Male': '男', 'Female': '女', 'Non-binary': '非二元', 'Prefer not to say': '不愿透露' }
  return map[g] || g
}

const riskLevelLabel = (level) => {
  const map = { 'Low Risk': '低风险', 'Medium Risk': '中风险', 'High Risk': '高风险' }
  return map[level] || level
}

const riskTagType = (level) => {
  const map = { 'Low Risk': 'success', 'Medium Risk': 'warning', 'High Risk': 'danger' }
  return map[level] || 'info'
}

const getScoreColor = (score) => {
  if (score >= 70) return '#f56c6c'
  if (score >= 40) return '#e6a23c'
  return '#67c23a'
}

const getProgressColor = (label) => {
  const map = { 'Low Risk': '#67c23a', 'Medium Risk': '#e6a23c', 'High Risk': '#f56c6c' }
  return map[label] || '#409eff'
}

const fetchStats = async () => {
  try {
    const res = await getAssessmentStats()
    if (res.code === 200) {
      stats.value = res.data
    }
  } catch (e) {
    console.error('获取统计失败:', e)
  }
}

const fetchRecords = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, per_page: pagination.per_page }
    if (filter.risk_level) params.risk_level = filter.risk_level
    if (filter.username) params.username = filter.username

    const res = await getAssessmentRecords(params)
    if (res.code === 200) {
      records.value = res.data.items || []
      pagination.total = res.data.total || 0
    }
  } catch (e) {
    ElMessage.error('获取记录失败')
  } finally {
    loading.value = false
  }
}

const showDetail = (row) => {
  currentRecord.value = row
  detailVisible.value = true
}

onMounted(() => {
  fetchStats()
  fetchRecords()
})
</script>

<style lang="scss" scoped>
.assessment-records-container {
  .stats-row {
    margin-bottom: 20px;
  }

  .filter-area {
    display: flex;
    align-items: center;
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .more-tag {
    font-size: 12px;
    color: #909399;
    margin-left: 4px;
  }

  .probability-section {
    .prob-bar {
      display: flex;
      align-items: center;
      margin-bottom: 12px;

      .prob-label {
        width: 70px;
        font-size: 13px;
        color: #606266;
        flex-shrink: 0;
      }

      .el-progress {
        flex: 1;
      }
    }
  }
}
</style>
