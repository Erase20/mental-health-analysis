<template>
  <div class="report-container">
    <!-- 生成报告 -->
    <div class="dashboard-card">
      <div class="card-header">
        <span class="title">生成分析报告</span>
      </div>
      <el-form :model="reportForm" label-width="100px">
        <el-form-item label="报告类型">
          <el-radio-group v-model="reportForm.type">
            <el-radio-button value="full">完整报告</el-radio-button>
            <el-radio-button value="risk">风险分析</el-radio-button>
            <el-radio-button value="cluster">聚类分析</el-radio-button>
            <el-radio-button value="model">模型评估</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="报告标题">
          <el-input v-model="reportForm.title" placeholder="请输入报告标题" style="width: 400px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="generating" @click="handleGenerate">
            <el-icon><Document /></el-icon>
            生成报告
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 报告预览 -->
    <div class="dashboard-card mt-20">
      <div class="card-header">
        <span class="title">报告预览</span>
        <el-button type="primary" text @click="fetchPreviewData">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
      
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="preview-stat">
            <div class="stat-label">总样本数</div>
            <div class="stat-value">{{ previewData.overview?.total_samples || 0 }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="preview-stat">
            <div class="stat-label">高风险人数</div>
            <div class="stat-value text-danger">
              {{ previewData.overview?.risk_distribution?.['High Risk'] || 0 }}
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="preview-stat">
            <div class="stat-label">中风险人数</div>
            <div class="stat-value text-warning">
              {{ previewData.overview?.risk_distribution?.['Medium Risk'] || 0 }}
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="preview-stat">
            <div class="stat-label">低风险人数</div>
            <div class="stat-value text-success">
              {{ previewData.overview?.risk_distribution?.['Low Risk'] || 0 }}
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 报告列表 -->
    <div class="dashboard-card mt-20">
      <div class="card-header">
        <span class="title">历史报告</span>
      </div>
      <el-table :data="reportList" border stripe>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleDownload(row)">
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { generateReport, getReportList, downloadReport, previewReportData } from '@/api/report'

const generating = ref(false)
const reportList = ref([])
const previewData = ref({})

const reportForm = ref({
  type: 'full',
  title: '心理健康用户画像分析报告'
})

const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

const formatDate = (timestamp) => {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}

const handleGenerate = async () => {
  generating.value = true
  try {
    const res = await generateReport(reportForm.value)
    if (res.code === 200) {
      ElMessage.success('报告生成成功')
      fetchReportList()
      // 自动下载
      handleDownload({ filename: res.data.filename })
    }
  } catch (error) {
    ElMessage.error(error.message || '报告生成失败')
  } finally {
    generating.value = false
  }
}

const fetchReportList = async () => {
  try {
    const res = await getReportList()
    if (res.code === 200) {
      reportList.value = res.data
    }
  } catch (error) {
    console.error('获取报告列表失败:', error)
  }
}

const fetchPreviewData = async () => {
  try {
    const res = await previewReportData()
    if (res.code === 200) {
      previewData.value = res.data
    }
  } catch (error) {
    console.error('获取预览数据失败:', error)
  }
}

const handleDownload = async (row) => {
  try {
    const blob = await downloadReport(row.filename)
    // 创建下载链接
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = row.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

onMounted(() => {
  fetchReportList()
  fetchPreviewData()
})
</script>

<style lang="scss" scoped>
.report-container {
  .mt-20 {
    margin-top: 20px;
  }
  
  .preview-stat {
    text-align: center;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 8px;
    
    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-bottom: 10px;
    }
    
    .stat-value {
      font-size: 28px;
      font-weight: 600;
      color: #303133;
      
      &.text-success {
        color: #67c23a;
      }
      
      &.text-warning {
        color: #e6a23c;
      }
      
      &.text-danger {
        color: #f56c6c;
      }
    }
  }
}
</style>
