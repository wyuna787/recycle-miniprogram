<script>
import request from './utils/request.js'
export default {
  onShow() {
    const check = () => {
      if (uni.getStorageSync('token')) {
        request({ url: '/api/account/me', showError: false }).catch(() => {})
      }
    }
    check()
    clearInterval(this.sessionCheckTimer)
    this.sessionCheckTimer = setInterval(check, 10000)
  },
  onHide() {
    clearInterval(this.sessionCheckTimer)
    this.sessionCheckTimer = null
  }
}
</script>
<style>
page { font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; background-color: #f3f5f7; font-size: 28rpx; color: #1e293b; }
</style>
