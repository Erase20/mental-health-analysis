/**
 * 验证工具函数
 */

/**
 * 验证邮箱
 */
export function isValidEmail(email) {
  const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return regex.test(email)
}

/**
 * 验证手机号
 */
export function isValidPhone(phone) {
  const regex = /^1[3-9]\d{9}$/
  return regex.test(phone)
}

/**
 * 验证密码强度
 * 至少6位，包含字母和数字
 */
export function isValidPassword(password) {
  if (password.length < 6) return false
  const hasLetter = /[a-zA-Z]/.test(password)
  const hasNumber = /\d/.test(password)
  return hasLetter && hasNumber
}

/**
 * 验证用户名
 * 3-20位，字母开头，可包含字母、数字、下划线
 */
export function isValidUsername(username) {
  const regex = /^[a-zA-Z][a-zA-Z0-9_]{2,19}$/
  return regex.test(username)
}
