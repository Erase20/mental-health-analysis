<template>
  <div class="data-container">
    <!-- 操作栏 -->
    <div class="dashboard-card">
      <div class="card-header">
        <span class="title">数据管理</span>
        <div class="action-group">
          <el-upload
            action=""
            :auto-upload="false"
            :on-change="handleFileChange"
            :show-file-list="false"
            accept=".csv,.xlsx,.xls"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              导入数据
            </el-button>
          </el-upload>
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </div>
      </div>
      <el-alert
        title="支持导入 CSV、Excel 格式的数据文件"
        type="info"
        :closable="false"
        show-icon
      />
    </div>
    
    <!-- 筛选栏 -->
    <div class="dashboard-card">
      <el-form :model="filter" inline>
        <el-form-item label="风险等级">
          <el-select v-model="filter.risk_level" placeholder="全部" clearable>
            <el-option label="低风险" value="Low Risk" />
            <el-option label="中风险" value="Medium Risk" />
            <el-option label="高风险" value="High Risk" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="filter.gender" placeholder="全部" clearable>
            <el-option label="男" value="Male" />
            <el-option label="女" value="Female" />
            <el-option label="其他" value="Other" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄组">
          <el-select v-model="filter.age_group" placeholder="全部" clearable>
            <el-option label="25岁及以下" value="25岁及以下" />
            <el-option label="26-35岁" value="26-35岁" />
            <el-option label="36-45岁" value="36-45岁" />
            <el-option label="46-55岁" value="46-55岁" />
            <el-option label="56岁以上" value="56岁以上" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 数据表格 -->
    <div class="dashboard-card">
      <el-table :data="dataList" border stripe v-loading="loading" height="600">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="age" label="年龄" width="80" />
        <el-table-column prop="gender" label="性别" width="100">
          <template #default="{ row }">{{ genderLabel(row.gender) }}</template>
        </el-table-column>
        <el-table-column prop="country" label="国家" width="120" />
        <el-table-column prop="risk_level" label="风险等级" width="120">
          <template #default="{ row }">
            <el-tag :type="getRiskTagType(row.risk_level)">
              {{ riskLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cluster_id" label="聚类" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.cluster_id !== null" type="info">
              {{ getClusterName(row.cluster_id) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="treatment" label="治疗" width="100">
          <template #default="{ row }">{{ yesNoLabel(row.treatment) }}</template>
        </el-table-column>
        <el-table-column prop="family_history" label="家族病史" width="100">
          <template #default="{ row }">{{ yesNoLabel(row.family_history) }}</template>
        </el-table-column>
        <el-table-column prop="work_interfere" label="工作干扰" width="120">
          <template #default="{ row }">{{ workInterfereLabel(row.work_interfere) }}</template>
        </el-table-column>
        <el-table-column prop="remote_work" label="远程工作" width="100">
          <template #default="{ row }">{{ yesNoLabel(row.remote_work) }}</template>
        </el-table-column>
        <el-table-column prop="tech_company" label="科技公司" width="100">
          <template #default="{ row }">{{ yesNoLabel(row.tech_company) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              查看
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="数据详情" width="800px">
      <el-descriptions :column="2" border v-if="currentRow">
        <el-descriptions-item label="ID">{{ currentRow.id }}</el-descriptions-item>
        <el-descriptions-item label="年龄">{{ currentRow.age }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ genderLabel(currentRow.gender) }}</el-descriptions-item>
        <el-descriptions-item label="国家">{{ currentRow.country }}</el-descriptions-item>
        <el-descriptions-item label="州/省">{{ currentRow.state }}</el-descriptions-item>
        <el-descriptions-item label="风险等级">
          <el-tag :type="getRiskTagType(currentRow.risk_level)">
            {{ riskLabel(currentRow.risk_level) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否自雇">{{ yesNoLabel(currentRow.self_employed) }}</el-descriptions-item>
        <el-descriptions-item label="家族病史">{{ yesNoLabel(currentRow.family_history) }}</el-descriptions-item>
        <el-descriptions-item label="是否治疗">{{ yesNoLabel(currentRow.treatment) }}</el-descriptions-item>
        <el-descriptions-item label="工作干扰">{{ workInterfereLabel(currentRow.work_interfere) }}</el-descriptions-item>
        <el-descriptions-item label="公司规模">{{ currentRow.no_employees }}</el-descriptions-item>
        <el-descriptions-item label="远程工作">{{ yesNoLabel(currentRow.remote_work) }}</el-descriptions-item>
        <el-descriptions-item label="科技公司">{{ yesNoLabel(currentRow.tech_company) }}</el-descriptions-item>
        <el-descriptions-item label="公司福利">{{ currentRow.benefits }}</el-descriptions-item>
        <el-descriptions-item label="关怀选项">{{ currentRow.care_options }}</el-descriptions-item>
        <el-descriptions-item label="健康项目">{{ currentRow.wellness_program }}</el-descriptions-item>
        <el-descriptions-item label="寻求帮助">{{ currentRow.seek_help }}</el-descriptions-item>
        <el-descriptions-item label="匿名性">{{ currentRow.anonymity }}</el-descriptions-item>
        <el-descriptions-item label="休假政策">{{ currentRow.leave }}</el-descriptions-item>
        <el-descriptions-item label="心理健康后果">{{ currentRow.mental_health_consequence }}</el-descriptions-item>
        <el-descriptions-item label="身体后果">{{ currentRow.phys_health_consequence }}</el-descriptions-item>
        <el-descriptions-item label="同事态度">{{ currentRow.coworkers }}</el-descriptions-item>
        <el-descriptions-item label="上级态度">{{ currentRow.supervisor }}</el-descriptions-item>
        <el-descriptions-item label="面试心理">{{ currentRow.mental_health_interview }}</el-descriptions-item>
        <el-descriptions-item label="面试身体">{{ currentRow.phys_health_interview }}</el-descriptions-item>
        <el-descriptions-item label="心理vs身体">{{ currentRow.mental_vs_physical }}</el-descriptions-item>
        <el-descriptions-item label="观察后果">{{ currentRow.obs_consequence }}</el-descriptions-item>
        <el-descriptions-item label="评论" :span="2">{{ currentRow.comments || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDataList, deleteData, uploadFile, exportData } from '@/api/data'

const loading = ref(false)
const dataList = ref([])
const detailVisible = ref(false)
const currentRow = ref(null)

const filter = ref({
  risk_level: '',
  gender: '',
  age_group: ''
})

const pagination = ref({
  page: 1,
  per_page: 20,
  total: 0
})

const getRiskTagType = (risk) => {
  const types = {
    'Low Risk': 'success',
    'Medium Risk': 'warning',
    'High Risk': 'danger'
  }
  return types[risk] || 'info'
}

// 下面三个函数只负责“展示翻译”，不会修改接口中的原始枚举值。
const riskLabel = (risk) => ({
  'Low Risk': '低风险',
  'Medium Risk': '中风险',
  'High Risk': '高风险'
}[risk] || risk || '-')

const genderLabel = (gender) => {
  const value = String(gender || '').trim().toLowerCase()
  if (['male', 'm', 'man'].includes(value)) return '男'
  if (['female', 'f', 'woman'].includes(value)) return '女'
  if (!value) return '未知'
  return '其他/不愿透露'
}

const yesNoLabel = (value) => {
  if (value === 'Yes') return '是'
  if (value === 'No') return '否'
  return value || '-'
}

const workInterfereLabel = (value) => ({
  Often: '经常',
  Sometimes: '有时',
  Rarely: '很少',
  Never: '从不',
  'Not applicable': '不适用'
}[value] || value || '-')

const getClusterName = (clusterId) => {
  const names = {
    0: '高风险群体',
    1: '中高风险群体',
    2: '中风险群体',
    3: '低风险群体',
    4: '超低风险群体'
  }
  return names[clusterId] || `群体_${clusterId}`
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      per_page: pagination.value.per_page,
      ...filter.value
    }
    
    const res = await getDataList(params)
    if (res.code === 200) {
      dataList.value = res.data.items
      pagination.value.total = res.data.total
    }
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filter.value = {
    risk_level: '',
    gender: '',
    age_group: ''
  }
  fetchData()
}

const viewDetail = (row) => {
  currentRow.value = row
  detailVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除这条数据吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteData(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const handleFileChange = async (file) => {
  // el-upload 关闭了自动上传，这里手动构造 multipart/form-data。
  const formData = new FormData()
  formData.append('file', file.raw)
  
  try {
    const res = await uploadFile(formData)
    if (res.code === 200) {
      ElMessage.success(res.message)
      fetchData()
    }
  } catch (error) {
    ElMessage.error('导入失败')
  }
}

const handleExport = async () => {
  try {
    const res = await exportData(filter.value)
    if (res.code === 200) {
      ElMessage.success('导出成功')
      // 下载文件
      window.open(res.data.download_url)
    }
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.data-container {
  .action-group {
    display: flex;
    gap: 10px;
  }
  
  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>
