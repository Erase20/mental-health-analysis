<template>
  <div class="settings-container">
    <el-tabs type="border-card">
      <el-tab-pane label="个人设置">
        <el-form :model="userForm" label-width="100px" style="max-width: 500px">
          <el-form-item label="用户名">
            <el-input v-model="userForm.username" disabled />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="userForm.email" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="userForm.phone" />
          </el-form-item>
          <el-form-item label="部门">
            <el-input v-model="userForm.department" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleUpdateProfile">保存修改</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      
      <el-tab-pane label="修改密码">
        <el-form 
          ref="passwordFormRef"
          :model="passwordForm" 
          :rules="passwordRules"
          label-width="100px" 
          style="max-width: 500px"
        >
          <el-form-item label="原密码" prop="old_password">
            <el-input v-model="passwordForm.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="passwordForm.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="changing" @click="handleChangePassword">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      
      <el-tab-pane label="系统信息">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="系统名称">心理健康用户画像分析与可视化系统</el-descriptions-item>
          <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
          <el-descriptions-item label="技术栈">Vue 3 + Flask + MySQL + Redis</el-descriptions-item>
          <el-descriptions-item label="机器学习">Scikit-learn + PySpark</el-descriptions-item>
          <el-descriptions-item label="可视化">ECharts 5</el-descriptions-item>
          <el-descriptions-item label="作者">毕业设计项目</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import { changePassword } from '@/api/auth'

const userStore = useUserStore()
const passwordFormRef = ref(null)
const changing = ref(false)

const userForm = ref({
  username: '',
  email: '',
  phone: '',
  department: ''
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.value.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const initUserForm = () => {
  if (userStore.userInfo) {
    userForm.value = { ...userStore.userInfo }
  }
}

const handleUpdateProfile = () => {
  ElMessage.success('个人资料更新成功')
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changing.value = true
      try {
        const res = await changePassword({
          old_password: passwordForm.value.old_password,
          new_password: passwordForm.value.new_password
        })
        if (res.code === 200) {
          ElMessage.success('密码修改成功')
          passwordForm.value = {
            old_password: '',
            new_password: '',
            confirm_password: ''
          }
        }
      } catch (error) {
        ElMessage.error(error.message || '密码修改失败')
      } finally {
        changing.value = false
      }
    }
  })
}

onMounted(() => {
  initUserForm()
})
</script>

<style lang="scss" scoped>
.settings-container {
  max-width: 800px;
}
</style>
