<template>
  <view class="page">
    <custom-navbar title="预付款资金池" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ currentUser.company_name || '中晨回收' }}</view>
          <view class="title">资金池管理</view>
          <view class="desc">
            回收商报价前需保证资金池余额充足，余额低于 {{ MIN_QUOTE_FUND }} 元不可报价。
          </view>
        </view>

        <view class="hero-icon">款</view>
      </view>

      <view class="balance-card">
        <view>
          <view class="balance-label">当前可用余额</view>
          <view class="balance-money">¥{{ formatMoney(fund.availableAmount) }}</view>
        </view>

        <view :class="['balance-status', canQuote ? 'safe' : 'danger']">
          {{ canQuote ? '可报价' : '不可报价' }}
        </view>
      </view>

      <view class="fund-breakdown">
        <view class="fund-cell">
          <view class="fund-cell-label">总余额</view>
          <view class="fund-cell-value">¥{{ formatMoney(fund.balance) }}</view>
        </view>
        <view class="fund-cell">
          <view class="fund-cell-label">冻结中</view>
          <view class="fund-cell-value">¥{{ formatMoney(fund.frozenAmount) }}</view>
        </view>
        <view class="fund-cell">
          <view class="fund-cell-label">已扣款</view>
          <view class="fund-cell-value">¥{{ formatMoney(fund.deductedAmount) }}</view>
        </view>
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

    <view class="notice-card">
      <view class="notice-title">报价规则</view>
      <view class="notice-line">1. 资金池余额低于 {{ MIN_QUOTE_FUND }} 元时，回收商员工不可报价。</view>
      <view class="notice-line">2. 报价金额不得大于资金池当前可用余额。</view>
      <view class="notice-line">3. 线下转账后需上传转账截图，由平台管理员审核。</view>
      <view class="notice-line">4. 审核通过后，金额才会进入资金池。</view>
    </view>

    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">提交充值申请</view>
          <view class="section-desc">上传线下转账截图，等待平台审核</view>
        </view>
      </view>

      <view class="form-item">
        <view class="label">充值金额</view>
        <input
          class="input"
          type="number"
          v-model="rechargeAmount"
          placeholder="请输入充值金额"
        />
      </view>

      <view class="form-item">
        <view class="label">转账截图</view>

        <view class="upload-box" @click="chooseImage">
          <image
            v-if="rechargeScreenshot"
            class="upload-img"
            :src="rechargeScreenshot"
            mode="aspectFill"
          />

          <view v-else class="upload-empty">
            <view class="upload-plus">+</view>
            <view>上传转账截图</view>
          </view>
        </view>
      </view>

      <button class="submit-btn" @click="submitRecharge">
        提交平台审核
      </button>
    </view>

    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">充值记录</view>
          <view class="section-desc">平台审核后自动更新资金池余额</view>
        </view>

        <view class="refresh-btn" @click="loadData">
          刷新
        </view>
      </view>

      <view v-if="myApplyList.length === 0" class="empty">
        暂无充值记录
      </view>

      <view
        v-for="item in myApplyList"
        :key="item.id"
        class="record-card"
      >
        <view class="record-head">
          <view>
            <view class="record-money">¥{{ formatMoney(item.amount) }}</view>
            <view class="record-time">{{ item.createTime }}</view>
          </view>

          <view :class="['record-status', item.status]">
            {{ statusText(item.status) }}
          </view>
        </view>

        <view class="record-info">
          <view class="info-row">
            <text>提交账号</text>
            <text>{{ item.applyUserName || '-' }}</text>
          </view>

          <view class="info-row">
            <text>所属公司</text>
            <text>{{ item.companyName || '-' }}</text>
          </view>

          <view class="info-row">
            <text>审核时间</text>
            <text>{{ item.payoutTime || '-' }}</text>
          </view>
        </view>

        <image
          v-if="item.screenshot"
          class="proof-img"
          :src="item.screenshot"
          mode="aspectFill"
          @click="previewImage(item.screenshot)"
        />

        <view v-if="item.rejectReason" class="reject-box">
          驳回原因：{{ item.rejectReason }}
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">资金流水</view>
          <view class="section-desc">冻结、扣款与释放记录</view>
        </view>
      </view>

      <view v-if="flowList.length === 0" class="empty">
        暂无资金流水
      </view>

      <view
        v-for="flow in flowList"
        :key="flow.id"
        class="flow-row"
      >
        <view class="flow-left">
          <view class="flow-type">{{ getFlowTypeText(flow.type) }}</view>
          <view class="flow-meta">{{ flow.orderNo ? '订单 ' + flow.orderNo + ' · ' : '' }}{{ flow.time }}</view>
        </view>

        <view :class="['flow-amount', flowAmountClass(flow.type)]">
          {{ flowAmountPrefix(flow.type) }}¥{{ formatMoney(flow.amount) }}
        </view>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { formatMoney } from '@/utils/moneyMock.js'
import { getNowText } from '@/utils/tradeFlow.js'
import { getCompanyFlows, getFlowTypeText } from '@/utils/fundFlow.js'
import { uploadImage } from '@/utils/request.js'
import { getFundPool, getFundFlows, applyRecharge, getRechargeApplies } from '@/api/fund.js'

const FUND_KEY = 'recyclerFundPoolList'
const APPLY_KEY = 'recyclerRechargeApplyList'
const MIN_QUOTE_FUND = 5000

const currentUser = ref({})
const fundList = ref([])
const applyList = ref([])
const flowList = ref([])

const rechargeAmount = ref('')
const rechargeScreenshot = ref('')

onShow(() => {
  currentUser.value = uni.getStorageSync('userInfo') ||
    uni.getStorageSync('currentUser') ||
    {}

  if (!currentUser.value.role) {
    uni.reLaunch({
      url: '/pages/login/login'
    })
    return
  }

  loadData()
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

// 含可用余额(总余额 - 冻结)的资金视图
const fund = computed(() => {
  const balance = Number(companyFund.value.balance || 0)
  const frozenAmount = Number(companyFund.value.frozenAmount || 0)
  const deductedAmount = Number(companyFund.value.deductedAmount || 0)

  return {
    balance,
    frozenAmount,
    deductedAmount,
    availableAmount: balance - frozenAmount
  }
})

const canQuote = computed(() => {
  return fund.value.availableAmount >= MIN_QUOTE_FUND
})

const myApplyList = computed(() => {
  return applyList.value.filter(item => {
    return Number(item.companyId) === Number(currentUser.value.company_id)
  })
})

const pendingList = computed(() => {
  return myApplyList.value.filter(item => item.status === 'pending')
})

const approvedList = computed(() => {
  return myApplyList.value.filter(item => item.status === 'approved')
})

const rejectedList = computed(() => {
  return myApplyList.value.filter(item => item.status === 'rejected')
})

// 释放/充值为入账(绿色 +),冻结/扣款/服务费为占用(红色 -)
function flowAmountClass(type) {
  return (type === 'recharge' || type === 'release') ? 'plus' : 'minus'
}

function flowAmountPrefix(type) {
  return (type === 'recharge' || type === 'release') ? '+' : '-'
}

async function loadData() {
  const companyId = Number(currentUser.value.company_id)

  try {
    const [poolRes, applyRes, flowRes] = await Promise.all([
      getFundPool(companyId),
      getRechargeApplies(),
      getFundFlows(companyId)
    ])

    fundList.value = [{
      companyId,
      companyName: poolRes.company_name || currentUser.value.company_name || '',
      balance: Number(poolRes.balance || 0),
      frozenAmount: Number(poolRes.frozen_amount || 0),
      deductedAmount: Number(poolRes.deducted_amount || 0),
      updatedTime: getNowText()
    }]

    applyList.value = (applyRes.list || []).map(item => ({
      id: item.id,
      companyId: Number(item.company_id),
      companyName: item.company_name || '',
      applyUserId: item.apply_user_id,
      applyUserName: item.apply_user_name || '',
      amount: Number(item.amount || 0),
      screenshot: item.proof_image || '',
      status: item.status,
      createTime: item.create_time || '',
      payoutTime: item.review_time || '',
      rejectReason: item.reject_reason || ''
    }))

    flowList.value = (flowRes.list || [])
      .filter(flow => flow.type !== 'platform_fee')
      .map(flow => ({
        id: flow.id,
        type: flow.type,
        orderNo: flow.order_no || '',
        time: flow.create_time || '',
        amount: Number(flow.amount || 0)
      }))
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  fundList.value = uni.getStorageSync(FUND_KEY) || []
  applyList.value = uni.getStorageSync(APPLY_KEY) || []
  flowList.value = getCompanyFlows(currentUser.value.company_id)
    .filter(flow => flow.type !== 'platform_fee')

  ensureCompanyFund()
}

function saveFundList() {
  uni.setStorageSync(FUND_KEY, fundList.value)
}

function saveApplyList() {
  uni.setStorageSync(APPLY_KEY, applyList.value)
}

function ensureCompanyFund() {
  const companyId = Number(currentUser.value.company_id)

  if (!companyId) return

  const existed = fundList.value.find(item => {
    return Number(item.companyId) === companyId
  })

  if (existed) return

  fundList.value.unshift({
    companyId,
    companyName: currentUser.value.company_name || `中晨回收${companyId}`,
    balance: 0,
    frozenAmount: 0,
    updatedTime: getNowText()
  })

  saveFundList()
}

function chooseImage() {
  uni.chooseImage({
    count: 1,
    success(res) {
      const tempPath = res.tempFilePaths[0]
      rechargeScreenshot.value = tempPath

      uni.showLoading({ title: '上传中', mask: true })
      uploadImage(tempPath)
        .then(url => {
          rechargeScreenshot.value = url
        })
        .catch(() => {})
        .finally(() => {
          uni.hideLoading()
        })
    }
  })
}

async function submitRecharge() {
  const amount = Number(rechargeAmount.value)

  if (!amount || amount <= 0) {
    uni.showToast({
      title: '请输入正确金额',
      icon: 'none'
    })
    return
  }

  if (!rechargeScreenshot.value) {
    uni.showToast({
      title: '请上传转账截图',
      icon: 'none'
    })
    return
  }

  try {
    await applyRecharge({
      company_id: Number(currentUser.value.company_id),
      amount,
      proof_image: rechargeScreenshot.value
    })

    rechargeAmount.value = ''
    rechargeScreenshot.value = ''

    uni.showToast({
      title: '已提交审核',
      icon: 'success'
    })

    await loadData()
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  const apply = {
    id: Date.now(),
    companyId: currentUser.value.company_id,
    companyName: currentUser.value.company_name,
    applyUserId: currentUser.value.id,
    applyUserName: currentUser.value.username,
    amount,
    screenshot: rechargeScreenshot.value,
    status: 'pending',
    createTime: getNowText(),
    payoutTime: '',
    payouterId: '',
    payouterName: '',
    rejectReason: ''
  }

  applyList.value.unshift(apply)
  saveApplyList()

  rechargeAmount.value = ''
  rechargeScreenshot.value = ''

  uni.showToast({
    title: '已提交审核',
    icon: 'success'
  })

  loadData()
}

function previewImage(url) {
  uni.previewImage({
    urls: [url],
    current: url
  })
}

function statusText(status) {
  const map = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已驳回'
  }

  return map[status] || status || '-'
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

.balance-card {
  margin-top: 30rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.balance-label {
  font-size: 25rpx;
  opacity: 0.9;
}

.balance-money {
  margin-top: 8rpx;
  font-size: 52rpx;
  font-weight: 600;
}

.balance-status {
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: #ffffff;
  font-size: 24rpx;
  font-weight: bold;
}

.balance-status.safe {
  color: #18a058;
}

.balance-status.danger {
  color: #ff5a3c;
}

.stats {
  display: flex;
  margin-top: 26rpx;
  gap: 16rpx;
}

.stat-item {
  flex: 1;
  padding: 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.2);
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

.notice-card,
.section {
  margin: 24rpx;
  padding: 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.notice-title,
.section-title {
  color: #222222;
  font-size: 32rpx;
  font-weight: 600;
}

.notice-line {
  margin-top: 14rpx;
  color: #666666;
  font-size: 25rpx;
  line-height: 38rpx;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28rpx;
}

.section-desc {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.refresh-btn {
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: #eef0f4;
  color: #374151;
  font-size: 24rpx;
  font-weight: bold;
}

.form-item {
  margin-bottom: 28rpx;
}

.label {
  margin-bottom: 14rpx;
  color: #333333;
  font-size: 26rpx;
  font-weight: bold;
}

.input {
  height: 88rpx;
  padding: 0 24rpx;
  border-radius: 22rpx;
  background: #f5f8fb;
  font-size: 30rpx;
  box-sizing: border-box;
}

.upload-box {
  height: 250rpx;
  border-radius: 24rpx;
  background: #f5f8fb;
  border: 2rpx dashed #cfe1ee;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.upload-img {
  width: 100%;
  height: 100%;
}

.upload-empty {
  color: #64748b;
  text-align: center;
  font-size: 25rpx;
}

.upload-plus {
  font-size: 54rpx;
  line-height: 54rpx;
  margin-bottom: 10rpx;
}

.submit-btn {
  height: 82rpx;
  line-height: 82rpx;
  border-radius: 999rpx;
  background: #17324d;
  color: #ffffff;
  font-size: 29rpx;
  font-weight: bold;
}

.submit-btn::after {
  border: none;
}

.empty {
  padding: 60rpx 30rpx;
  border-radius: 16rpx;
  background: #f6f7f9;
  text-align: center;
  color: #999999;
  font-size: 27rpx;
}

.record-card {
  margin-top: 22rpx;
  padding: 26rpx;
  border-radius: 16rpx;
  background: #f6f7f9;
}

.record-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.record-money {
  color: #ff5a3c;
  font-size: 40rpx;
  font-weight: 600;
}

.record-time {
  margin-top: 8rpx;
  color: #999999;
  font-size: 24rpx;
}

.record-status {
  padding: 9rpx 16rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
  font-weight: bold;
}

.record-status.pending {
  background: #fff7e6;
  color: #d97706;
}

.record-status.approved {
  background: #ecfdf3;
  color: #18a058;
}

.record-status.rejected {
  background: #fff0eb;
  color: #ff5a3c;
}

.record-info {
  margin-top: 20rpx;
  padding: 18rpx;
  border-radius: 18rpx;
  background: #ffffff;
}

.info-row {
  display: flex;
  justify-content: space-between;
  color: #666666;
  font-size: 24rpx;
  line-height: 40rpx;
}

.proof-img {
  width: 180rpx;
  height: 180rpx;
  margin-top: 18rpx;
  border-radius: 18rpx;
  background: #eeeeee;
}

.reject-box {
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 18rpx;
  background: #fff0eb;
  color: #ff5a3c;
  font-size: 24rpx;
  line-height: 36rpx;
}

.fund-breakdown {
  margin-top: 18rpx;
  display: flex;
  gap: 16rpx;
}

.fund-cell {
  flex: 1;
  padding: 18rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.18);
  text-align: center;
}

.fund-cell-label {
  font-size: 24rpx;
  opacity: 0.9;
}

.fund-cell-value {
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: bold;
}

.flow-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #eef1f4;
}

.flow-row:last-child {
  border-bottom: none;
}

.flow-type {
  color: #222222;
  font-size: 27rpx;
  font-weight: bold;
}

.flow-meta {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 24rpx;
}

.flow-amount {
  font-size: 30rpx;
  font-weight: 600;
}

.flow-amount.plus {
  color: #18a058;
}

.flow-amount.minus {
  color: #ff5a3c;
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
