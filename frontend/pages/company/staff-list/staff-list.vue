<template>
  <view class="page">
    <view class="hero">
      <view class="hero-top">
        <view class="back-btn" @click="goBack">‹</view>
        <view class="hero-main">
          <view class="hello">{{ currentUser.company_name || '我的公司' }}</view>
          <view class="title">员工账号</view>
          <view class="desc">查看本公司全部账号、角色与权限状态。</view>
        </view>
        <view class="hero-icon">员</view>
      </view>

      <view class="stats">
        <view class="stat-item">
          <view class="stat-number">{{ staffList.length }}</view>
          <view class="stat-label">账号总数</view>
        </view>
        <view class="stat-line"></view>
        <view class="stat-item">
          <view class="stat-number">{{ approvedCount }}</view>
          <view class="stat-label">已通过</view>
        </view>
        <view class="stat-line"></view>
        <view class="stat-item">
          <view class="stat-number">{{ pendingCount }}</view>
          <view class="stat-label">待审核</view>
        </view>
      </view>
    </view>

    <view class="staff-card">
      <view class="name">新增员工</view>
      <input v-model="newStaff.nickname" placeholder="员工姓名" />
      <input v-model="newStaff.phone" placeholder="员工登录账号" />
      <input v-model="newStaff.password" password placeholder="初始密码（至少3位）" />
      <picker v-if="currentUser.role==='recycler_owner'" :range="['报价员工','库管']" @change="newStaff.role = Number($event.detail.value)===1 ? 'recycler_keeper' : 'recycler_staff'"><view>角色：{{ newStaff.role==='recycler_keeper'?'库管':'报价员工' }} ›</view></picker>
      <button @click="addStaff">新增并审核通过</button>
    </view>
    <view v-if="staffList.length === 0" class="empty">暂无员工账号</view>

    <view
      v-for="item in staffList"
      :key="item.id"
      class="staff-card"
    >
      <view class="card-head">
        <view class="avatar">{{ roleAvatar(item.role) }}</view>
        <view class="head-main">
          <view class="name-row">
            <text class="name">{{ item.username || item.nickname || '未命名' }}</text>
            <text v-if="item.is_self" class="self-tag">本人</text>
          </view>
          <view class="role">{{ roleText(item.role) }}</view>
        </view>
        <view :class="['status-pill', item.status]">{{ statusText(item.status) }}</view>
      </view>

      <view class="info">
        <view class="info-row">
          <text>手机号</text>
          <text>{{ item.phone || '-' }}</text>
        </view>
        <view class="info-row">
          <text>加入时间</text>
          <text>{{ item.created_at || '-' }}</text>
        </view>
        <view v-if="!item.is_owner" class="info-row">
          <text>权限</text>
          <text>{{ permissionText(item) }}</text>
        </view>
        <view v-if="item.reject_reason" class="info-row">
          <text>驳回原因</text>
          <text>{{ item.reject_reason }}</text>
        </view>
      </view>
      <view v-if="!item.is_owner && !item.is_self" class="actions">
        <button v-if="item.status === 'pending'" @click="manage(item,'approve')">审核通过</button>
        <button v-if="item.status === 'pending'" @click="manage(item,'reject')">拒绝加入</button>
        <button v-if="item.role==='merchant_staff' && item.status==='approved'" @click="toggleSell(item)">{{ item.can_accept_quote?'关闭成交权限':'允许确认成交' }}</button>
        <button v-if="item.status === 'approved'" @click="manage(item,'disable')">移除员工</button>
        <button v-if="item.status === 'disabled'" @click="manage(item,'enable')">恢复员工</button>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { merchantAPI } from '@/utils/api.js'
import { getCompanyStaff, manageCompanyStaff, addCompanyStaff } from '@/api/account.js'

const currentUser = ref({})
const staffList = ref([])
const newStaff = ref({nickname:'',phone:'',password:'',role:'recycler_staff'})

onShow(async () => {
  currentUser.value = uni.getStorageSync('currentUser') || uni.getStorageSync('userInfo') || {}

  if (!currentUser.value.role) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }

  try {
    const res = await getCompanyStaff()
    staffList.value = res.list || []
  } catch (error) {
    staffList.value = []
  }
})

const approvedCount = computed(() => staffList.value.filter(i => i.status === 'approved').length)
const pendingCount = computed(() => staffList.value.filter(i => i.status === 'pending').length)

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.reLaunch({ url: '/pages/home/home' })
  }
}

function roleAvatar(role) {
  const map = {
    merchant_owner: '商',
    merchant_staff: '员',
    recycler_owner: '收',
    recycler_keeper: '库',
    recycler_staff: '抢'
  }
  return map[role] || '员'
}

function roleText(role) {
  const map = {
    merchant_owner: '商家老板',
    merchant_staff: '商家员工',
    recycler_owner: '回收商老板',
    recycler_keeper: '回收商库管',
    recycler_staff: '回收商员工'
  }
  return map[role] || role || '-'
}

function statusText(status) {
  const map = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已驳回', disabled: '已停用'
  }
  return map[status] || '-'
}

function permissionText(item) {
  const list = []
  if (item.can_create_inquiry) list.push('可发起询价')
  if (item.can_view_all_inquiry) list.push('可看全部询价')
  if (item.can_accept_quote) list.push('可同意卖出')
  if (item.can_manage_staff) list.push('可管理员工')
  return list.length ? list.join('、') : '基础权限'
}
async function manage(item, action) {
  uni.showModal({ title: '员工账号管理', content: `确认${ {approve:'通过',reject:'拒绝',disable:'移除',enable:'恢复'}[action]}员工 ${item.username}？`, success: async res => {
    if (!res.confirm) return
    try { await manageCompanyStaff(item.id, action); const result = await getCompanyStaff(); staffList.value = result.list || [] } catch(e) { /* request displays error */ }
  } })
}
async function addStaff() {
  if (!newStaff.value.nickname.trim() || !newStaff.value.phone.trim() || newStaff.value.password.length < 3) return uni.showToast({ title:'请填写姓名、账号和至少3位密码', icon:'none' })
  try {
    await addCompanyStaff({ ...newStaff.value, role: currentUser.value.role==='merchant_owner'?'merchant_staff':newStaff.value.role, company_type:currentUser.value.company_type, company_id:currentUser.value.company_id })
    newStaff.value={nickname:'',phone:'',password:'',role:'recycler_staff'}
    const result=await getCompanyStaff();staffList.value=result.list||[]
    uni.showToast({title:'员工已新增',icon:'success'})
  } catch(e) { /* request displays error */ }
}
async function toggleSell(item) {
  try {
    await merchantAPI.updateStaffPermissions(item.id, {can_create_inquiry:item.can_create_inquiry,can_view_all_inquiry:item.can_view_all_inquiry,can_accept_quote:!item.can_accept_quote,can_manage_staff:item.can_manage_staff})
    const result=await getCompanyStaff();staffList.value=result.list||[]
  } catch(e) { /* request displays error */ }
}
</script>





<style scoped>

.staff-card input{background:#f4f6f8;border-radius:16rpx;padding:20rpx;margin:18rpx 0}.staff-card button{background:#344054;color:#fff;font-size:26rpx;margin-top:18rpx;}
.actions{display:flex;gap:20rpx;margin-top:20rpx}.actions button{font-size:24rpx;background:#344054;color:#fff;}
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
  align-items: flex-start;
}

.hero-main {
  flex: 1;
}

.back-btn {
  color: #fff;
  font-size: 70rpx;
  line-height: 60rpx;
  padding: 0 18rpx 0 0;
  opacity: 0.9;
  font-weight: 300;
}

.hello {
  font-size: 26rpx;
  opacity: 0.9;
}

.title {
  margin-top: 10rpx;
  font-size: 44rpx;
  font-weight: 600;
}

.desc {
  margin-top: 12rpx;
  font-size: 25rpx;
  opacity: 0.9;
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
  align-items: center;
  margin-top: 30rpx;
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-number {
  font-size: 40rpx;
  font-weight: 600;
}

.stat-label {
  margin-top: 6rpx;
  font-size: 24rpx;
  opacity: 0.9;
}

.stat-line {
  width: 1rpx;
  height: 44rpx;
  background: rgba(255, 255, 255, 0.45);
}

.empty {
  margin: 40rpx 24rpx;
  padding: 70rpx 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  color: #999999;
  text-align: center;
  font-size: 28rpx;
}

.staff-card {
  margin: 0 24rpx 22rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.card-head {
  display: flex;
  align-items: center;
}

.avatar {
  width: 76rpx;
  height: 76rpx;
  margin-right: 20rpx;
  border-radius: 24rpx;
  background: #17324d;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 600;
}

.head-main {
  flex: 1;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.name {
  color: #111111;
  font-size: 30rpx;
  font-weight: 600;
}

.self-tag {
  padding: 2rpx 12rpx;
  border-radius: 999rpx;
  background: #eef0f4;
  color: #17324d;
  font-size: 24rpx;
}

.role {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 24rpx;
}

.status-pill {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
  font-weight: bold;
}

.status-pill.approved {
  background: #ecfdf3;
  color: #18a058;
}

.status-pill.pending {
  background: #fff7e6;
  color: #d97706;
}

.status-pill.rejected {
  background: #fff0eb;
  color: #ff5a3c;
}

.info {
  margin-top: 20rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: #f6f7f9;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  color: #666666;
  font-size: 24rpx;
  line-height: 42rpx;
}

.info-row text:last-child {
  text-align: right;
  color: #333333;
}

.safe-bottom {
  height: 60rpx;
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
