<template>
  <view class="page">
    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">当前账号</view>
          <view class="title">{{ roleText(currentUser.role) }}</view>
          <view class="desc">
            查看账号资料、公司信息和当前权限状态。
          </view>
        </view>

        <view class="hero-icon">
          {{ avatarText }}
        </view>
      </view>

      <view class="profile-mini">
        <view>
          <view class="profile-name">{{ currentUser.username || '未登录' }}</view>
          <view class="profile-phone">{{ currentUser.phone || '-' }}</view>
        </view>

        <view :class="['status-pill', currentUser.status || 'pending']">
          {{ accountStatusText(currentUser.status) }}
        </view>
      </view>
    </view>

    <view v-if="['merchant_owner','merchant_staff'].includes(currentUser.role)" class="section">
      <view class="section-title">公司保证金与结算</view>
      <view class="info-card">
        <view>保证金额度 ¥{{ formatMoney(merchantDeposit.deposit_amount || 0) }}</view>
        <view>{{ merchantDeposit.settlement_mode==='ship'?'保证金额度内发货即到款':'确认收货后到款' }}</view>
        <view v-if="merchantDeposit.pending_application">保证金申请待平台核实：¥{{ formatMoney(merchantDeposit.pending_application.amount) }}</view>
        <view v-if="currentUser.role==='merchant_owner' && !merchantDeposit.pending_application">
          <input class="form-input" type="digit" v-model="depositAmount" placeholder="申请缴纳保证金金额" />
          <textarea class="form-input" v-model="depositRemark" placeholder="付款说明或备注（可选）" />
          <button :disabled="depositBusy" @click="applyDeposit">申请缴纳保证金</button>
          <view>提交申请不代表到账，须经平台核实确认。</view>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-title">账号资料</view>

      <view class="info-card">
        <view class="info-row">
          <text>手机号</text>
          <text>{{ currentUser.phone || '-' }}</text>
        </view>

        <view class="info-row">
          <text>身份</text>
          <text>{{ roleText(currentUser.role) }}</text>
        </view>

        <view class="info-row">
          <text>公司名称</text>
          <text>{{ currentUser.company_name || '-' }}</text>
        </view>

        <view class="info-row">
          <text>公司类型</text>
          <text>{{ companyTypeText(currentUser.company_type) }}</text>
        </view>

        <view class="info-row">
          <text>公司ID</text>
          <text>{{ currentUser.company_id ?? '-' }}</text>
        </view>

        <view class="info-row">
          <text>当前权限</text>
          <text>{{ permissionSummary }}</text>
        </view>

        <view class="info-row">
          <text>账号状态</text>
          <text>{{ accountStatusText(currentUser.status) }}</text>
        </view>
      </view>
    </view>

    <view v-if="isRecyclerRole(currentUser.role)" class="section">
      <view class="section-title">资金池</view>

      <view class="fund-card">
        <view>
          <view class="fund-label">当前可用余额</view>
          <view class="fund-money">¥{{ formatMoney(companyFund.balance) }}</view>
        </view>

        <view :class="['fund-status', canQuoteByFund ? 'safe' : 'danger']">
          {{ canQuoteByFund ? '可报价' : '不可报价' }}
        </view>
      </view>

      <view class="fund-note">
        资金池余额低于 {{ MIN_QUOTE_FUND }} 元时，回收商员工不可报价。
      </view>
    </view>

    <view class="section">
      <view class="section-title">账号操作</view>

      <view class="action-card">
        <view class="action-row" @click="openPasswordPopup">
          <view>
            <view class="action-title">修改密码</view>
            <view class="action-desc">验证原密码后设置新登录密码</view>
          </view>

          <view class="action-arrow">›</view>
        </view>

        <view class="action-row danger" @click="logout">
          <view>
            <view class="action-title">退出登录</view>
            <view class="action-desc">退出当前账号并返回登录页</view>
          </view>

          <view class="action-arrow">›</view>
        </view>
      </view>
    </view>

    <view v-if="passwordPopupVisible" class="mask" @click="closePasswordPopup">
      <view class="popup" @click.stop>
        <view class="popup-title">修改密码</view>
        <view class="popup-desc">为账号 {{ currentUser.phone || '' }} 设置新登录密码</view>

        <view class="form-item">
          <view class="form-label">原密码</view>
          <input
            class="form-input"
            password
            v-model="passwordForm.oldPassword"
            placeholder="请输入当前密码"
          />
        </view>

        <view class="form-item">
          <view class="form-label">新密码</view>
          <input
            class="form-input"
            password
            v-model="passwordForm.newPassword"
            placeholder="至少3位"
          />
        </view>

        <view class="form-item">
          <view class="form-label">确认新密码</view>
          <input
            class="form-input"
            password
            v-model="passwordForm.confirmPassword"
            placeholder="请再次输入新密码"
          />
        </view>

        <view class="popup-actions">
          <view class="popup-btn cancel" @click="closePasswordPopup">取消</view>
          <view class="popup-btn confirm" @click="submitPassword">确认修改</view>
        </view>
      </view>
    </view>

    <view v-if="currentUser.role==='recycler_owner'" class="section">
      <view class="section-title">公司收货信息</view>
      <input class="pwd-input" v-model="shippingContact.contact_name" placeholder="收件人姓名" />
      <input class="pwd-input" v-model="shippingContact.contact_phone" placeholder="收件电话" />
      <textarea class="pwd-input" v-model="shippingContact.address" placeholder="详细收货地址" />
      <button :disabled="savingContact" @click="saveShippingContact">保存收货信息</button>
      <view class="hint">成交后商家可查看，用于填写寄件信息。</view>
    </view>
    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { get, post } from '@/utils/request.js'
import { clearAccountSession } from '@/utils/session.js'
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { formatMoney } from '@/utils/moneyMock.js'
import { changePassword as changePasswordApi } from '@/api/account.js'

const FUND_KEY = 'recyclerFundPoolList'
const MIN_QUOTE_FUND = 5000

const currentUser = ref({})
const fundList = ref([])
const merchantDeposit=ref({}),depositAmount=ref(''),depositRemark=ref(''),depositBusy=ref(false)
async function applyDeposit(){
 if(depositBusy.value)return
 const amount=Number(depositAmount.value)
 if(!Number.isFinite(amount)||amount<=0)return uni.showToast({title:'请输入有效金额',icon:'none'})
 depositBusy.value=true
 try{await post('/api/merchant/deposit/apply',{amount,remark:depositRemark.value});merchantDeposit.value=await get('/api/merchant/deposit');uni.showToast({title:'已提交核实',icon:'success'})}catch(e){}finally{depositBusy.value=false}
}
const shippingContact=ref({contact_name:'',contact_phone:'',address:''}),savingContact=ref(false)
onShow(async()=>{
 const user=uni.getStorageSync('userInfo')||uni.getStorageSync('currentUser')||{}
 if(['merchant_owner','merchant_staff'].includes(user.role)){try{merchantDeposit.value=await get('/api/merchant/deposit')}catch(e){merchantDeposit.value={}}}
 if(user.role==='recycler_owner'){try{shippingContact.value=await get('/api/recycler/shipping-contact')}catch(e){}}
})
async function saveShippingContact(){
 if(savingContact.value)return
 if(Object.values(shippingContact.value).some(v=>!String(v).trim()))return uni.showToast({title:'请填写完整收货信息',icon:'none'})
 savingContact.value=true
 try{shippingContact.value=await post('/api/recycler/shipping-contact',shippingContact.value);uni.showToast({title:'已保存',icon:'success'})}catch(e){}finally{savingContact.value=false}
}

const passwordPopupVisible = ref(false)
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

onShow(() => {
  currentUser.value = uni.getStorageSync('currentUser') || {}
  fundList.value = uni.getStorageSync(FUND_KEY) || []

  if (!currentUser.value.role) {
    uni.reLaunch({
      url: '/pages/login/login'
    })
  }
})

const avatarText = computed(() => {
  const role = currentUser.value.role

  if (role === 'platform_admin') return '管'
  if (role === 'merchant_owner') return '商'
  if (role === 'merchant_staff') return '员'
  if (role === 'recycler_owner') return '收'
  if (role === 'recycler_keeper') return '库'
  if (role === 'recycler_staff') return '抢'

  const name = currentUser.value.username || '账'
  return name.slice(0, 1)
})

const companyFund = computed(() => {
  const companyId = Number(currentUser.value.company_id)

  const fund = fundList.value.find(item => {
    return Number(item.companyId) === companyId
  })

  if (fund) return fund

  return {
    companyId,
    companyName: currentUser.value.company_name || '',
    balance: 0,
    frozenAmount: 0,
    updatedTime: ''
  }
})

const canQuoteByFund = computed(() => {
  return Number(companyFund.value.balance || 0) >= MIN_QUOTE_FUND
})

const permissionSummary = computed(() => {
  const role = currentUser.value.role

  const map = {
    platform_admin: '平台全部权限',
    merchant_owner: '商家全部权限',
    merchant_staff: '商家员工权限',
    recycler_owner: '回收商全部权限',
    recycler_keeper: '库管权限',
    recycler_staff: '员工个人数据权限'
  }

  return map[role] || '-'
})

function isRecyclerRole(role) {
  return role === 'recycler_owner' ||
    role === 'recycler_keeper' ||
    role === 'recycler_staff'
}

function roleText(role) {
  const map = {
    platform_admin: '平台管理员',
    merchant_owner: '商家老板',
    merchant_staff: '商家员工',
    recycler_owner: '回收商老板',
    recycler_keeper: '回收商库管',
    recycler_staff: '回收商员工'
  }

  return map[role] || role || '未登录'
}

function companyTypeText(type) {
  const map = {
    merchant: '商家',
    recycler: '回收商',
    platform: '平台'
  }

  return map[type] || '-'
}

function accountStatusText(status) {
  const map = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已驳回'
  }

  return map[status] || '-'
}

function openPasswordPopup() {
  passwordForm.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  passwordPopupVisible.value = true
}

function closePasswordPopup() {
  passwordPopupVisible.value = false
}

async function submitPassword() {
  const { oldPassword, newPassword, confirmPassword } = passwordForm.value

  if (!oldPassword) {
    uni.showToast({ title: '请输入原密码', icon: 'none' })
    return
  }

  if (!newPassword || newPassword.length < 3) {
    uni.showToast({ title: '新密码至少3位', icon: 'none' })
    return
  }

  if (newPassword === oldPassword) {
    uni.showToast({ title: '新密码不能与原密码相同', icon: 'none' })
    return
  }

  if (newPassword !== confirmPassword) {
    uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' })
    return
  }

  try {
    await changePasswordApi({
      old_password: oldPassword,
      new_password: newPassword
    })
  } catch (error) {
    // 错误提示已在请求层统一弹出
    return
  }

  closePasswordPopup()

  uni.showModal({
    title: '修改成功',
    content: '密码已更新，请使用新密码重新登录。',
    showCancel: false,
    confirmText: '重新登录',
    success: () => {
      clearAccountSession()

      uni.reLaunch({
        url: '/pages/login/login'
      })
    }
  })
}

function logout() {
  uni.showModal({
    title: '确认退出',
    content: '确定要退出当前账号吗？',
    confirmText: '退出',
    cancelText: '取消',
    confirmColor: '#ff5a3c',
    success: res => {
      if (!res.confirm) return

      clearAccountSession()

      uni.reLaunch({
        url: '/pages/login/login'
      })
    }
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

.title {
  margin-top: 10rpx;
  font-size: 46rpx;
  font-weight: 600;
}

.desc {
  margin-top: 12rpx;
  font-size: 25rpx;
  line-height: 38rpx;
  opacity: 0.92;
}

.hero-icon {
  width: 92rpx;
  height: 92rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.22);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  font-weight: 600;
}

.profile-mini {
  margin-top: 32rpx;
  padding: 26rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profile-name {
  font-size: 34rpx;
  font-weight: 600;
}

.profile-phone {
  margin-top: 8rpx;
  font-size: 24rpx;
  opacity: 0.9;
}

.status-pill {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #ffffff;
  font-size: 24rpx;
  font-weight: bold;
}

.status-pill.approved {
  color: #18a058;
}

.status-pill.pending {
  color: #d97706;
}

.status-pill.rejected {
  color: #ff5a3c;
}

.section {
  margin: 24rpx;
}

.section-title {
  margin-bottom: 18rpx;
  color: #222222;
  font-size: 34rpx;
  font-weight: 600;
}

.info-card,
.action-card,
.fund-card {
  padding: 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #eef1f4;
  color: #666666;
  font-size: 26rpx;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row text:last-child {
  text-align: right;
  color: #222222;
  font-weight: bold;
}

.fund-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fund-label {
  color: #64748b;
  font-size: 24rpx;
}

.fund-money {
  margin-top: 8rpx;
  color: #ff5a3c;
  font-size: 48rpx;
  font-weight: 600;
}

.fund-status {
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
  font-weight: bold;
}

.fund-status.safe {
  background: #ecfdf3;
  color: #18a058;
}

.fund-status.danger {
  background: #fff0eb;
  color: #ff5a3c;
}

.fund-note {
  margin-top: 18rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 36rpx;
}

.action-card {
  padding: 0 30rpx;
}

.action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 0;
  border-bottom: 1rpx solid #eef1f4;
}

.action-row:last-child {
  border-bottom: none;
}

.action-title {
  color: #222222;
  font-size: 30rpx;
  font-weight: 600;
}

.action-desc {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.action-row.danger .action-title {
  color: #ff5a3c;
}

.action-arrow {
  color: #c7c9cc;
  font-size: 52rpx;
  font-weight: 300;
}

.safe-bottom {
  height: 60rpx;
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
  padding: 40rpx 36rpx 36rpx;
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

.popup-desc {
  margin-top: 12rpx;
  text-align: center;
  color: #777777;
  font-size: 25rpx;
}

.form-item {
  margin-top: 26rpx;
}

.form-label {
  margin-bottom: 12rpx;
  color: #333333;
  font-size: 25rpx;
  font-weight: bold;
}

.form-input {
  height: 84rpx;
  padding: 0 24rpx;
  border-radius: 20rpx;
  background: #f6f7f9;
  font-size: 28rpx;
  box-sizing: border-box;
}

.popup-actions {
  display: flex;
  gap: 18rpx;
  margin-top: 36rpx;
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

.popup-btn.confirm {
  background: #17324d;
  color: #ffffff;
}


.page .hero{padding-top:calc(var(--status-bar-height) + 40rpx)}


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
