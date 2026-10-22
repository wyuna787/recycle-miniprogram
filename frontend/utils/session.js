// 登录失效、退出和换账号统一清理，旧账号数据不得留在新账号中。
export function clearAccountSession() {
  uni.clearStorageSync()
  for (let index = 0; index < 3; index++) {
    uni.removeTabBarBadge({ index, fail() {} })
  }
  uni.$emit('account-session-cleared')
}

export function expireAccountSession(expectedToken) {
  if (expectedToken && uni.getStorageSync('token') !== expectedToken) return
  clearAccountSession()
  uni.reLaunch({ url: '/pages/login/login' })
}
