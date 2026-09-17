<template>
  <div class="profile-detail-container">
    <el-page-header @back="goBack" title="用户画像详情" />
    
    <div v-if="profileData" class="profile-content">
      <!-- 基本信息 -->
      <el-row :gutter="20">
        <el-col :xs="24" :lg="8">
          <div class="dashboard-card">
            <div class="card-header">
              <span class="title">风险概况</span>
            </div>
            <div class="risk-overview">
              <div class="risk-score">
                <el-progress
                  type="dashboard"
                  :percentage="profileData.profile.risk_score"
                  :color="progressColors"
                  :stroke-width="10"
                />
                <div class="score-label">风险评分</div>
              </div>
              <div class="risk-level">
                <span class="label">风险等级:</span>
                <el-tag :type="getRiskTagType(profileData.profile.risk_level)" size="large">
                  {{ profileData.profile.risk_level }}
                </el-tag>
              </div>
              <div class="cluster-info">
                <span class="label">所属群体:</span>
                <el-tag type="info">{{ profileData.profile.cluster_name }}</el-tag>
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :lg="16">
          <div class="dashboard-card">
            <div class="card-header">
              <span class="title">画像标签</span>
            </div>
            <div class="tags-section">
              <el-tag
                v-for="tag in profileData.profile.tags"
                :key="tag"
                size="large"
                effect="dark"
                style="margin: 5px"
              >
                {{ tag }}
              </el-tag>
            </div>
            <el-divider />
            <div class="description">
              <h4>画像描述</h4>
              <p>{{ profileData.profile.description }}</p>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <!-- 关键特征和建议 -->
      <el-row :gutter="20" class="mt-20">
        <el-col :xs="24" :lg="12">
          <div class="dashboard-card">
            <div class="card-header">
              <span class="title">关键特征</span>
            </div>
            <el-descriptions :column="1" border>
              <el-descriptions-item
                v-for="(value, key) in profileData.profile.key_features"
                :key="key"
                :label="key"
              >
                {{ value }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <div class="dashboard-card">
            <div class="card-header">
              <span class="title">健康建议</span>
            </div>
            <el-timeline>
              <el-timeline-item
                v-for="(rec, index) in profileData.profile.recommendations"
                :key="index"
                :type="index === 0 ? 'primary' : ''"
              >
                {{ rec }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-col>
      </el-row>
      
      <!-- 原始数据 -->
      <el-row :gutter="20" class="mt-20">
        <el-col :span="24">
          <div class="dashboard-card">
            <div class="card-header">
              <span class="title">原始数据</span>
            </div>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="年龄">{{ profileData.raw_data?.age }}</el-descriptions-item>
              <el-descriptions-item label="性别">{{ profileData.raw_data?.gender }}</el-descriptions-item>
              <el-descriptions-item label="国家">{{ profileData.raw_data?.country }}</el-descriptions-item>
              <el-descriptions-item label="是否治疗">{{ profileData.raw_data?.treatment }}</el-descriptions-item>
              <el-descriptions-item label="家族病史">{{ profileData.raw_data?.family_history }}</el-descriptions-item>
              <el-descriptions-item label="工作干扰">{{ profileData.raw_data?.work_interfere }}</el-descriptions-item>
              <el-descriptions-item label="远程工作">{{ profileData.raw_data?.remote_work }}</el-descriptions-item>
              <el-descriptions-item label="科技公司">{{ profileData.raw_data?.tech_company }}</el-descriptions-item>
              <el-descriptions-item label="公司福利">{{ profileData.raw_data?.benefits }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
      </el-row>
      
      <!-- 相似画像 -->
      <el-row :gutter="20" class="mt-20" v-if="similarProfiles.length > 0">
        <el-col :span="24">
          <div class="dashboard-card">
            <div class="card-header">
              <span class="title">相似画像</span>
            </div>
            <el-table :data="similarProfiles" border stripe>
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="risk_level" label="风险等级" width="120">
                <template #default="{ row }">
                  <el-tag :type="getRiskTagType(row.risk_level)">
                    {{ row.risk_level }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="risk_score" label="风险评分" width="120" />
              <el-table-column prop="cluster_name" label="所属群体" width="120" />
              <el-table-column label="标签">
                <template #default="{ row }">
                  <el-tag
                    v-for="tag in row.tags"
                    :key="tag"
                    size="small"
                    style="margin-right: 5px"
                  >
                    {{ tag }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button type="primary" size="small" @click="viewSimilar(row.id)">
                    查看
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProfileDetail, getSimilarProfiles } from '@/api/user'

const route = useRoute()
const router = useRouter()

const profileId = route.params.id
const profileData = ref(null)
const similarProfiles = ref([])

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

const fetchProfileDetail = async () => {
  try {
    const res = await getProfileDetail(profileId)
    if (res.code === 200) {
      profileData.value = res.data
    }
  } catch (error) {
    ElMessage.error('获取画像详情失败')
  }
}

const fetchSimilarProfiles = async () => {
  try {
    const res = await getSimilarProfiles(profileId, { limit: 5 })
    if (res.code === 200) {
      similarProfiles.value = res.data
    }
  } catch (error) {
    console.error('获取相似画像失败:', error)
  }
}

const viewSimilar = (id) => {
  router.push(`/profiles/${id}`)
  // 重新加载页面数据
  setTimeout(() => {
    window.location.reload()
  }, 100)
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchProfileDetail()
  fetchSimilarProfiles()
})
</script>

<style lang="scss" scoped>
.profile-detail-container {
  .profile-content {
    margin-top: 20px;
  }
  
  .mt-20 {
    margin-top: 20px;
  }
  
  .risk-overview {
    text-align: center;
    
    .risk-score {
      margin-bottom: 20px;
      
      .score-label {
        margin-top: 10px;
        font-size: 16px;
        color: #606266;
      }
    }
    
    .risk-level, .cluster-info {
      margin: 15px 0;
      
      .label {
        margin-right: 10px;
        color: #909399;
      }
    }
  }
  
  .tags-section {
    margin-bottom: 20px;
  }
  
  .description {
    h4 {
      margin-bottom: 10px;
      color: #303133;
    }
    
    p {
      color: #606266;
      line-height: 1.6;
    }
  }
}
</style>
