<template>
  <div class="user-report-container">
    <div class="dashboard-card">
      <div class="card-header">
        <span class="title">我的报告</span>
        <el-button type="primary" :loading="generating" @click="handleGenerate">
          <el-icon><DocumentChecked /></el-icon>
          生成个人报告
        </el-button>
      </div>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        您可以生成个人心理健康评估报告（PDF格式），报告将基于您的自评数据进行生成。
      </el-alert>

      <!-- 报告列表 -->
      <el-table :data="reportList" border stripe v-loading="loading" empty-text="暂无报告，请先进行自评后生成报告">
        <el-table-column prop="filename" label="报告名称" min-width="250">
          <template #default="{ row }">
            <el-icon><Document /></el-icon>
            <span style="margin-left: 8px">{{ row.filename }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="生成时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleDownload(row)">
              <el-icon><Download /></el-icon>
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
import { generateReport, getReportList, downloadReport } from '@/api/report'

const loading = ref(false)
const generating = ref(false)
const reportList = ref([])

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}

const fetchReportList = async () => {
  loading.value = true
  try {
    const res = await getReportList()
    if (res.code === 200) {
      reportList.value = res.data || []
    }
  } catch (error) {
    console.error('获取报告列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleGenerate = async () => {
  generating.value = true
  try {
    const res = await generateReport({ type: 'personal', title: '个人心理健康评估报告' })
    if (res.code === 200) {
      ElMessage.success('报告生成成功')
      fetchReportList()
    }
  } catch (error) {
    ElMessage.error(error.message || '报告生成失败')
  } finally {
    generating.value = false
  }
}

const handleDownload = async (row) => {
  try {
    const res = await downloadReport(row.filename)
    // 创建下载链接
    const blob = new Blob([res], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = row.filename
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

onMounted(() => {
  fetchReportList()
})
</script>

<style lang="scss" scoped>
.user-report-container {
  max-width: 900px;
}
</style>
