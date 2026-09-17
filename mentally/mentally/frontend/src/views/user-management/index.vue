<template>
  <div class="user-management-container">
    <div class="dashboard-card">
      <div class="card-header">
        <span class="title">用户账号管理</span>
        <div class="filter-area">
          <el-input
            v-model="filter.keyword"
            placeholder="搜索用户名/邮箱"
            clearable
            style="width: 180px; margin-right: 10px"
            @clear="fetchUsers"
            @keyup.enter="fetchUsers"
          />
          <el-select v-model="filter.role" placeholder="角色" clearable style="width: 120px; margin-right: 10px" @change="fetchUsers">
            <el-option label="管理员" value="admin" />
            <el-option label="分析师" value="analyst" />
            <el-option label="普通用户" value="user" />
          </el-select>
          <el-button type="primary" @click="fetchUsers">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
        </div>
      </div>

      <el-table :data="userList" border stripe v-loading="loading" empty-text="暂无用户">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="login_count" label="登录次数" width="90" />
        <el-table-column prop="last_login" label="最后登录" width="170" />
        <el-table-column prop="created_at" label="注册时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              :type="row.is_active ? 'warning' : 'success'"
              size="small"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-popconfirm
              title="确定要删除该用户吗？该操作不可恢复！"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small" link :disabled="row.role === 'admin'">
                  删除
                </el-button>
              </template>
            </el-popconfirm>
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
          @current-change="fetchUsers"
          @size-change="fetchUsers"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserAccounts, deleteUserAccount, toggleUserStatus } from '@/api/user'

const loading = ref(false)
const userList = ref([])

const filter = reactive({
  keyword: '',
  role: ''
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const roleLabel = (role) => {
  const map = { admin: '管理员', analyst: '分析师', user: '普通用户' }
  return map[role] || role
}

const roleTagType = (role) => {
  const map = { admin: 'danger', analyst: 'warning', user: '' }
  return map[role] || 'info'
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, per_page: pagination.per_page }
    if (filter.keyword) params.keyword = filter.keyword
    if (filter.role) params.role = filter.role

    const res = await getUserAccounts(params)
    if (res.code === 200) {
      userList.value = res.data.items || []
      pagination.total = res.data.total || 0
    }
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleToggleStatus = async (row) => {
  try {
    const res = await toggleUserStatus(row.id)
    if (res.code === 200) {
      ElMessage.success(res.message)
      fetchUsers()
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    const res = await deleteUserAccount(row.id)
    if (res.code === 200) {
      ElMessage.success('用户已删除')
      fetchUsers()
    }
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style lang="scss" scoped>
.user-management-container {
  .filter-area {
    display: flex;
    align-items: center;
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
