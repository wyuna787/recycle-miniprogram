<template>
  <view class="page">
    <custom-navbar title="员工审核" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ currentUser.username || '公司管理员' }}</view>
          <view class="desc">
            审核本公司员工/库管账号申请，通过后员工方可登录使用。
          </view>
        </view>

        <view class="hero-icon">审</view>
      </view>

      <view class="stats">
        <view class="stat-item">
          <view class="stat-number">{{ pendingList.length }}</view>
          <view class="stat-label">待审核</view>
        </view>

        <view class="stat-item">
          <view class="stat-number">{{ approvedList.length }}</view>
          <view class="stat-label">已通过</view>
        </view>

        <view class="stat-item">
          <view class="stat-number">{{ rejectedList.length }}</view>
          <view class="stat-label">已驳回</view>
        </view>
      </view>
    </view>

    <view class="company-bar">
      <text class="company-label">所属公司</text>
      <text class="company-name">{{ currentUser.company_name || '-' }}</text>
    </view>

    <view class="tabs">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab', activeTab === tab.key ? 'active' : '']"
        @click="activeTab = tab.key"
      >
        {{ tab.name }}
        <text v-if="tab.badge" class="tab-badge">{{ tab.badge }}</text>
      </view>
    </view>

    <view class="section-head">
      <view class="section-title">{{ sectionTitle }}</view>
      <view class="section-desc">{{ sectionDesc }}</view>
    </view>

    <view v-if="displayList.length === 0" class="empty">
      {{ emptyText }}
    </view>

    <view
      v-for="item in displayList"
      :key="item.id"
      class="card"
    >
      <view class="card-head">
        <view>
          <view class="card-title">{{ item.nickname || '未命名员工' }}</view>
          <view class="card-sub">{{ roleText(item.role) }}</view>
        </view>

        <view :class="['status-pill', statusClass(item.status)]">
          {{ statusText(item.status) }}
        </view>
      </view>

      <view class="info-box">
        <view class="info-row">
          <text>员工姓名</text>
          <text>{{ item.nickname || '-' }}</text>
        </view>

        <view class="info-row">
          <text>手机号</text>
          <text>{{ item.phone || '-' }}</text>
        </view>

        <view class="info-row">
          <text>申请角色</text>
          <text>{{ roleText(item.role) }}</text>
        </view>

        <view class="info-row">
          <text>所属公司</text>
          <text>{{ item.company_name || '-' }}</text>
        </view>

        <view class="info-row">
          <text>申请时间</text>
          <text>{{ item.created_at || '-' }}</text>
        </view>

        <view class="info-row">
          <text>账号状态</text>
          <text>{{ statusText(item.status) }}</text>
        </view>

        <view v-if="item.apply_reason" class="info-row">
          <text>申请说明</text>
          <text>{{ item.apply_reason }}</text>
        </view>

        <view v-if="item.status === 'rejected' && item.reject_reason" class="info-row">
          <text>驳回原因</text>
          <text>{{ item.reject_reason }}</text>
        </view>

        <view v-if="item.status === 'approved' && item.approved_at" class="info-row">
          <text>通过时间</text>
          <text>{{ item.approved_at }}</text>
        </view>
      </view>

      <view v-if="item.status === 'pending'" class="action-row">
        <button class="reject-btn" @click="openReject(item)">
          驳回
        </button>

        <button class="approve-btn" @click="handleApprove(item)">
          通过
        </button>
      </view>
    </view>

    <view v-if="rejectPopupVisible" class="mask" @click="closeRejectPopup">
      <view class="popup" @click.stop>
        <view class="popup-title">驳回员工申请</view>

        <view class="form-item">
          <view class="label">驳回原因</view>
          <textarea
            class="textarea"
            v-model="rejectReason"
            placeholder="请输入驳回原因"
          />
        </view>

        <view class="popup-actions">
          <view class="popup-btn cancel" @click="closeRejectPopup">
            取消
          </view>

          <view class="popup-btn danger" @click="submitReject">
            确认驳回
          </view>
        </view>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  getAccountState,
  approveAccount,
  rejectAccount,
  roleText,
  statusText,
  isStaffRole
} from '@/utils/accountMock.js'

const currentUser = ref({})
const accountState = ref(getAccountState())
const activeTab = ref('pending')

const rejectPopupVisible = ref(false)
const rejectTarget = ref(null)
const rejectReason = ref('')

const OWNER_ROLES = ['merchant_owner', 'recycler_owner']

onShow(() => {
  currentUser.value = uni.getStorageSync('currentUser') || {}

  if (!OWNER_ROLES.includes(currentUser.value.role)) {
    uni.showToast({
      title: '暂无员工审核权限',
      icon: 'none'
    })

    uni.reLaunch({
      url: '/pages/home/home'
    })
    return
  }

  loadData()
})

const companyStaffList = computed(() => {
  const user = currentUser.value
  const accounts = accountState.value.accounts || []

  return accounts.filter(item => isCompanyStaff(item, user))
})

const pendingList = computed(() => {
  return companyStaffList.value.filter(item => item.status === 'pending')
})

const approvedList = computed(() => {
  return companyStaffList.value.filter(item => item.status === 'approved')
})

const rejectedList = computed(() => {
  return companyStaffList.value.filter(item => item.status === 'rejected')
})

const tabs = computed(() => {
  return [
    {
      key: 'pending',
      name: '待审核',
      badge: pendingList.value.length || ''
    },
    {
      key: 'approved',
      name: '已通过',
      badge: ''
    },
    {
      key: 'rejected',
      name: '已驳回',
      badge: ''
    },
    {
      key: 'all',
      name: '全部',
      badge: ''
    }
  ]
})

const displayList = computed(() => {
  if (activeTab.value === 'pending') return pendingList.value
  if (activeTab.value === 'approved') return approvedList.value
  if (activeTab.value === 'rejected') return rejectedList.value
  return companyStaffList.value
})

const sectionTitle = computed(() => {
  const map = {
    pending: '待审核申请',
    approved: '已通过员工',
    rejected: '已驳回申请',
    all: '全部员工申请'
  }

  return map[activeTab.value] || '员工申请'
})

const sectionDesc = computed(() => {
  if (currentUser.value.role === 'merchant_owner') {
    return '仅展示本公司商家员工账号申请'
  }

  return '仅展示本公司回收商员工与库管账号申请'
})

const emptyText = computed(() => {
  const map = {
    pending: '暂无待审核的员工申请',
    approved: '暂无已通过的员工',
    rejected: '暂无已驳回的申请',
    all: '暂无员工申请记录'
  }

  return map[activeTab.value] || '暂无数据'
})

function isCompanyStaff(account, owner) {
  if (!account || !owner) return false
  if (!isStaffRole(account.role)) return false
  if (account.company_type !== owner.company_type) return false
  if (Number(account.company_id) !== Number(owner.company_id)) return false

  if (owner.role === 'merchant_owner') {
    return account.role === 'merchant_staff'
  }

  if (owner.role === 'recycler_owner') {
    return account.role === 'recycler_staff' || account.role === 'recycler_keeper'
  }

  return false
}

function loadData() {
  accountState.value = getAccountState()
}

function statusClass(status) {
  if (status === 'approved') return 'success'
  if (status === 'rejected') return 'danger'
  return 'waiting'
}

function handleApprove(item) {
  uni.showModal({
    title: '确认通过',
    content: `确认通过 ${item.nickname || '该员工'} 的账号申请吗？`,
    confirmText: '通过',
    confirmColor: '#4b5563',
    success: res => {
      if (!res.confirm) return

      const result = approveAccount(item.id)

      if (!result.ok) {
        uni.showToast({
          title: result.message,
          icon: 'none'
        })
        return
      }

      loadData()

      uni.showToast({
        title: '已通过',
        icon: 'success'
      })
    }
  })
}

function openReject(item) {
  rejectTarget.value = item
  rejectReason.value = ''
  rejectPopupVisible.value = true
}

function closeRejectPopup() {
  rejectPopupVisible.value = false
  rejectTarget.value = null
  rejectReason.value = ''
}

function submitReject() {
  if (!rejectReason.value.trim()) {
    uni.showToast({
      title: '请填写驳回原因',
      icon: 'none'
    })
    return
  }

  const item = rejectTarget.value

  if (!item) return

  const result = rejectAccount(item.id, rejectReason.value.trim())

  if (!result.ok) {
    uni.showToast({
      title: result.message,
      icon: 'none'
    })
    return
  }

  closeRejectPopup()
  loadData()

  uni.showToast({
    title: '已驳回',
    icon: 'success'
  })
}
</script>





<style scoped>

.page {
  min-height: 100vh;
  background: #f3f5f7;
  box-sizing: border-box;
}

.hero {
  margin: 24rpx;
  padding: 34rpx;
  padding-top: calc(var(--status-bar-height) + 60rpx);
  border-radius: 16rpx;
  background: #17324d;
  color: #ffffff;
  box-shadow: none;
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.hello {
  font-size: 28rpx;
  opacity: 0.9;
}

.desc {
  margin-top: 12rpx;
  font-size: 25rpx;
  line-height: 38rpx;
  opacity: 0.92;
}

.hero-icon {
  width: 84rpx;
  height: 84rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  font-weight: 600;
}

.stats {
  display: flex;
  margin-top: 34rpx;
  gap: 16rpx;
}

.stat-item {
  flex: 1;
  padding: 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.22);
  text-align: center;
}

.stat-number {
  font-size: 40rpx;
  font-weight: 600;
}

.stat-label {
  margin-top: 6rpx;
  font-size: 24rpx;
}

.company-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 24rpx 24rpx;
  padding: 24rpx 28rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: none;
}

.company-label {
  color: #888888;
  font-size: 24rpx;
}

.company-name {
  color: #111111;
  font-size: 28rpx;
  font-weight: bold;
}

.tabs {
  display: flex;
  margin: 0 24rpx 24rpx;
  padding: 8rpx;
  border-radius: 999rpx;
  background: #ffffff;
  box-shadow: none;
}

.tab {
  position: relative;
  flex: 1;
  height: 72rpx;
  line-height: 72rpx;
  text-align: center;
  border-radius: 999rpx;
  color: #64748b;
  font-size: 25rpx;
  font-weight: bold;
}

.tab.active {
  background: #17324d;
  color: #ffffff;
}

.tab-badge {
  position: absolute;
  right: 8rpx;
  top: -8rpx;
  min-width: 30rpx;
  height: 30rpx;
  line-height: 30rpx;
  border-radius: 999rpx;
  background: #ff5a3c;
  color: #ffffff;
  font-size: 24rpx;
}

.section-head {
  margin: 0 24rpx 24rpx;
}

.section-title {
  color: #222222;
  font-size: 34rpx;
  font-weight: 600;
}

.section-desc {
  margin-top: 8rpx;
  color: #888888;
  font-size: 24rpx;
  line-height: 36rpx;
}

.empty {
  margin: 0 24rpx 40rpx;
  padding: 70rpx 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  color: #999999;
  text-align: center;
  font-size: 28rpx;
}

.card {
  margin: 0 24rpx 24rpx;
  padding: 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.card-title {
  color: #111111;
  font-size: 32rpx;
  font-weight: 600;
}

.card-sub {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.status-pill {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
  font-weight: bold;
}

.status-pill.waiting {
  background: #fff7e6;
  color: #d97706;
}

.status-pill.success {
  background: #ecfdf3;
  color: #18a058;
}

.status-pill.danger {
  background: #fff0eb;
  color: #ff5a3c;
}

.info-box {
  margin-top: 24rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: #f6f7f9;
}

.info-row {
  display: flex;
  justify-content: space-between;
  color: #666666;
  font-size: 24rpx;
  line-height: 42rpx;
  gap: 20rpx;
}

.info-row text:last-child {
  flex: 1;
  text-align: right;
  color: #333333;
}

.action-row {
  display: flex;
  gap: 18rpx;
  margin-top: 26rpx;
}

.reject-btn,
.approve-btn {
  flex: 1;
  height: 78rpx;
  line-height: 78rpx;
  border-radius: 999rpx;
  font-size: 27rpx;
  font-weight: bold;
}

.reject-btn {
  background: #fff0eb;
  color: #ff5a3c;
}

.approve-btn {
  background: #17324d;
  color: #ffffff;
}

.reject-btn::after,
.approve-btn::after {
  border: none;
}

.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  box-sizing: border-box;
}

.popup {
  width: 100%;
  padding: 36rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-sizing: border-box;
}

.popup-title {
  text-align: center;
  color: #111111;
  font-size: 36rpx;
  font-weight: 600;
}

.form-item {
  margin-top: 28rpx;
}

.label {
  margin-bottom: 14rpx;
  color: #333333;
  font-size: 26rpx;
  font-weight: bold;
}

.textarea {
  width: 100%;
  min-height: 150rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f5f8fb;
  font-size: 28rpx;
  box-sizing: border-box;
}

.popup-actions {
  display: flex;
  gap: 18rpx;
  margin-top: 32rpx;
}

.popup-btn {
  flex: 1;
  height: 82rpx;
  line-height: 82rpx;
  text-align: center;
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: bold;
}

.popup-btn.cancel {
  background: #f1f2f4;
  color: #555555;
}

.popup-btn.danger {
  background: #ff5a3c;
  color: #ffffff;
}

.safe-bottom {
  height: 50rpx;
}



/* BUSINESS_THEME_START */
/* Shared business design tokens. Imported in scoped page styles for mini program compatibility. */
.page,.board {font-family:"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif;background:#f3f5f7;color:#1e293b;box-sizing:border-box}
.hero {background:#17324d;color:#fff;box-shadow:none;border-radius:16rpx;padding:32rpx;margin:24rpx}
.hero .title {font-size:40rpx;font-weight:600;letter-spacing:0;line-height:1.4}
.hero .hello,.hero .desc {opacity:1;color:#dce7f0;line-height:1.6}
.hero-icon,.mini-program-pill {display:none}
.section,.card,.main-card,.panel,.compact,.report,.order-card,.info-card,.profile-card,.data-card,.flow-card {box-shadow:none;border-radius:16rpx;border:1rpx solid #e2e8f0;background:#fff}
.section-title,.heading,.card-title,.device-name {font-weight:600;color:#17324d}
.input,.search-input,.pwd-input,.order-search {background:#f7f9fb;border:1rpx solid #dce3eb;border-radius:10rpx;color:#1e293b;font-size:28rpx;box-sizing:border-box}
.input,.pwd-input {min-height:88rpx}
.order-search{height:88rpx;padding:0 24rpx;margin:24rpx;background:#fff}
.hint,.muted,.card-sub,.section-desc,.order-time,.owner-note,.preview-title {color:#64748b;font-size:24rpx;line-height:1.6}
.tabs,.tabs-card,.mode-tabs {border-radius:12rpx;box-shadow:none;background:#e8edf2}
.tab,.tab-item,.mode-tab {border-radius:8rpx;color:#475569;line-height:1.5}
.tab.active,.tab-item.active,.mode-tab.active {background:#17324d;color:#fff;box-shadow:none;border-radius:8rpx}
.primary-btn,.save-btn,.submit-btn,.confirm-btn {background:#17324d;color:#fff;box-shadow:none;border-radius:10rpx;font-weight:600;min-height:88rpx}
.price,.strong,.money,.amount,.rate-value {font-variant-numeric:tabular-nums;letter-spacing:0;font-weight:600}
.board .price {color:#17324d;font-size:34rpx}
.board .red,.bad,.danger,.error {color:#c43737}
.board .compact {padding:24rpx;margin:16rpx 0}
.board .summary{color:#475569;line-height:1.6}
.board .merchant {color:#475569;align-items:center}
.board .entry{color:#17324d;background:#eef3f7;border-radius:8rpx;padding:12rpx;font-size:24rpx}
.board button{border-radius:10rpx;min-height:88rpx;background:#17324d;font-size:28rpx}
.board .search-row{display:flex;align-items:center;background:#fff;border:1rpx solid #dce3eb;border-radius:12rpx;padding:0 20rpx;margin:16rpx 0 24rpx;gap:14rpx}
.search-row image{width:32rpx;height:32rpx;flex-shrink:0}
.board .search{flex:1;min-width:0;margin:0;padding:0;height:88rpx;border:0;background:transparent;border-radius:0}
.search-row text{color:#64748b;font-size:24rpx;padding:18rpx 0}
.empty,.empty-card,.empty-inline {padding:48rpx 24rpx;text-align:center;color:#64748b;font-size:26rpx;line-height:1.6}
.status-pill,.state,.order-status {font-size:24rpx;white-space:normal}
.report .row text:first-child{color:#64748b;flex-shrink:0}
.report .row.bad text{color:#c43737}
.info-row text:last-child {max-width:65%;text-align:right;overflow-wrap:anywhere}

/* BUSINESS_THEME_END */



</style>
