<template>
  <div class="profiles-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8">
        <div class="stat-card">
          <div class="stat-title">总画像数</div>
          <div class="stat-value">{{ statistics.total || 0 }}</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <div class="stat-card stat-card-warning">
          <div class="stat-title">高风险画像</div>
          <div class="stat-value">{{ statistics.risk_distribution?.['High Risk'] || 0 }}</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <div class="stat-card stat-card-success">
          <div class="stat-title">低风险画像</div>
          <div class="stat-value">{{ statistics.risk_distribution?.['Low Risk'] || 0 }}</div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 筛选栏 -->
    <div class="dashboard-card mt-20">
      <div class="card-header">
        <span class="title">用户画像列表</span>
        <div class="filter-group">
          <el-select v-model="filter.risk_level" placeholder="风险等级" clearable @change="fetchProfiles">
            <el-option label="低风险" value="Low Risk" />
            <el-option label="中风险" value="Medium Risk" />
            <el-option label="高风险" value="High Risk" />
          </el-select>
          <el-select v-model="filter.cluster_id" placeholder="所属群体" clearable @change="fetchProfiles">
            <el-option label="高风险群体" :value="0" />
            <el-option label="中高风险群体" :value="1" />
            <el-option label="中风险群体" :value="2" />
            <el-option label="低风险群体" :value="3" />
          </el-select>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索关键词"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
      
      <!-- 画像列表 -->
      <el-table :data="profileList" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="risk_level" label="风险等级" width="120">
          <template #default="{ row }">
            <el-tag :type="getRiskTagType(row.risk_level)">
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_score" label="风险评分" width="120">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.risk_score" 
              :color="progressColors"
              :show-text="false"
              style="width: 80px"
            />
            <span>{{ row.risk_score }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="cluster_name" label="所属群体" width="120" />
        <el-table-column label="标签" min-width="200">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.tags"
              :key="tag"
              size="small"
              style="margin-right: 5px; margin-bottom: 5px"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关键特征" min-width="200">
          <template #default="{ row }">
            <div v-for="(value, key) in row.key_features" :key="key" class="feature-item">
              <span class="feature-key">{{ key }}:</span>
              <span class="feature-value">{{ value }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row.id)">
              查看
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
          @size-change="fetchProfiles"
          @current-change="fetchProfiles"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProfiles, getProfileStatistics, searchProfiles } from '@/api/user'

const router = useRouter()

const loading = ref(false)
const profileList = ref([])
const statistics = ref({})
const searchKeyword = ref('')

const filter = ref({
  risk_level: '',
  cluster_id: null
})

const pagination = ref({
  page: 1,
  per_page: 20,
  total: 0
})

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

const fetchProfiles = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      per_page: pagination.value.per_page
    }
    // 只添加有效的筛选参数，避免传 null/空字符串
    if (filter.value.risk_level) {
      params.risk_level = filter.value.risk_level
    }
    if (filter.value.cluster_id !== null && filter.value.cluster_id !== undefined && filter.value.cluster_id !== '') {
      params.cluster_id = filter.value.cluster_id
    }
    
    const res = await getProfiles(params)
    if (res.code === 200) {
      profileList.value = res.data.items
      pagination.value.total = res.data.total
    }
  } catch (error) {
    ElMessage.error('获取画像列表失败')
  } finally {
    loading.value = false
  }
}

const fetchStatistics = async () => {
  try {
    const res = await getProfileStatistics()
    if (res.code === 200) {
      statistics.value = res.data
    }
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

const handleSearch = async () => {
  if (!searchKeyword.value) {
    fetchProfiles()
    return
  }
  
  loading.value = true
  try {
    const res = await searchProfiles({
      keyword: searchKeyword.value,
      page: pagination.value.page,
      per_page: pagination.value.per_page
    })
    if (res.code === 200) {
      profileList.value = res.data.items
      pagination.value.total = res.data.total
    }
  } catch (error) {
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

const viewDetail = (id) => {
  router.push(`/profiles/${id}`)
}

onMounted(() => {
  fetchProfiles()
  fetchStatistics()
})
</script>

<style lang="scss" scoped>
.profiles-container {
  .mt-20 {
    margin-top: 20px;
  }
  
  .filter-group {
    display: flex;
    gap: 10px;
  }
  
  .feature-item {
    display: inline-block;
    margin-right: 10px;
    font-size: 12px;
    
    .feature-key {
      color: #909399;
    }
    
    .feature-value {
      color: #606266;
      font-weight: 500;
    }
  }
  
  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>
