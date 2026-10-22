<template>
  <view class="page">
    <custom-navbar title="中晨回收报价" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ currentUser.username || '中晨回收' }}</view>
          <view class="title">填写报价</view>
          <view class="desc">
            输入回收商完整报价金额，系统自动计算商家端可见金额。
          </view>
        </view>

        <view class="hero-icon">报</view>
      </view>

      <view class="quota-card">
        <view>
          <view class="quota-label">预付款可用额度</view>
          <view class="quota-money">¥{{ formatMoney(companyFund.balance) }}</view>
        </view>

        <view :class="['quota-status', canQuoteByFund ? 'safe' : 'danger']">
          {{ canQuoteByFund ? '可报价' : '不可报价' }}
        </view>
      </view>
    </view>

    <view v-if="!inquiry" class="empty">
      未找到询价单
    </view>

    <view v-else>
      <view v-if="!canQuoteByFund" class="warning-card">
        <view class="warning-title">预付款额度不足</view>
        <view class="warning-desc">
          当前可用额度低于 {{ MIN_QUOTE_FUND }} 元，暂不可报价。请先由回收商老板或库管提交预付款凭证，平台审核通过后再报价。
        </view>

        <button class="warning-btn" @click="goFundPage">
          去提交预付款凭证
        </button>
      </view>

      <view v-if="isFinishedForRecycler(inquiry)" class="warning-card gray">
        <view class="warning-title">该询价单已结束</view>
        <view class="warning-desc">
          {{ finishedText }}
        </view>
      </view>

      <view class="card">
        <view class="section-title">设备信息</view>

        <view class="row">
          <text>设备</text>
          <text>{{ getDeviceTitle(inquiry) }}</text>
        </view>

        <view class="row">
          <text>设备类型</text>
          <text>{{ inquiry.deviceType || inquiry.device_type || '-' }}</text>
        </view>

        <view class="row">
          <text>存储容量</text>
          <text>{{ inquiry.storage || '-' }}</text>
        </view>

        <view class="row">
          <text>机身颜色</text>
          <text>{{ inquiry.color || '-' }}</text>
        </view>

        <view class="row">
          <text>保修时长</text>
          <text>{{ inquiry.warranty || '-' }}</text>
        </view>

        <view class="row">
          <text>购买渠道</text>
          <text>{{ inquiry.channel || '-' }}</text>
        </view>

        <view class="row">
          <text>商家公司</text>
          <text>{{ inquiry.merchantCompanyName || inquiry.company_name || '-' }}</text>
        </view>
      </view>

      <view class="card">
        <view class="section-title">报价信息</view>

        <view v-if="myQuote" class="old-quote-box">
          <view class="old-quote-title">当前我的报价</view>

          <view class="old-quote-money">
            ¥{{ formatMoney(myQuote.recyclerQuoteAmount || myQuote.amount) }}
          </view>

          <view class="old-quote-desc">
            报价时间：{{ myQuote.quoteTime || '-' }}
          </view>
        </view>

        <view class="form-item">
          <view class="label">完整报价金额</view>
          <input
            class="input"
            type="number"
            v-model="price"
            placeholder="请输入回收商完整报价金额"
          />
        </view>

        <view v-if="price" class="calc-card">
          <view class="calc-row">
            <text>商家基础可见金额</text>
            <text>¥{{ formatMoney(ppayoutAmount.merchantBaseAmount) }}</text>
          </view>

          <view class="calc-tip">
            {{ ppayoutAmount.merchantTip }}
          </view>

          <view v-if="overBalance" class="calc-warn">
            报价金额超出当前可用额度 ¥{{ formatMoney(balanceNumber) }}，无法提交。
          </view>
        </view>

        <view class="form-item">
          <view class="label">报价有效期</view>
          <input
            class="input"
            v-model="validDays"
            placeholder="例如：3天 / 今日有效"
          />
        </view>

        <view class="form-item">
          <view class="label">报价备注</view>
          <textarea
            class="textarea"
            v-model="remark"
            placeholder="例如：需到货后复检、配件齐全按此价"
          />
        </view>

        <view v-if="myQuote" class="form-item">
          <view class="label">修改原因</view>
          <textarea
            class="textarea"
            v-model="updateReason"
            placeholder="修改报价必须填写原因"
          />
        </view>
      </view>


      <button
        class="btn"
        :disabled="!canSubmit"
        @click="submitQuote"
      >
        {{ myQuote ? '确认修改报价' : '提交报价' }}
      </button>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  buildQuoteAmountSnapshot,
  formatMoney
} from '@/utils/moneyMock.js'
import { getNowText, getDeviceTitle } from '@/utils/tradeFlow.js'

const FUND_KEY = 'recyclerFundPoolList'
const MIN_QUOTE_FUND = 5000

const currentUser = ref({})
const inquiryId = ref(0)
const inquiryList = ref([])
const fundList = ref([])

const price = ref('')
const validDays = ref('')
const remark = ref('')
const updateReason = ref('')

onLoad(options => {
  currentUser.value = uni.getStorageSync('currentUser') || {}

  if (!currentUser.value.role) {
    uni.reLaunch({
      url: '/pages/login/login'
    })
    return
  }

  inquiryId.value = Number(options.id || 0)
  loadData()
  initForm()
})

// 当前报价金额（数值），统一供校验与提示使用
// 可用余额 = 总余额 - 冻结金额（已被其他成交订单占用的部分不能再报价）
const amountNumber = computed(() => Number(price.value) || 0)
const balanceNumber = computed(() => {
  return Number(companyFund.value.balance || 0) - Number(companyFund.value.frozenAmount || 0)
})
const overBalance = computed(() => amountNumber.value > balanceNumber.value)

const inquiry = computed(() => {
  return inquiryList.value.find(item => Number(item.id) === Number(inquiryId.value))
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
  return balanceNumber.value >= MIN_QUOTE_FUND
})

const ppayoutAmount = computed(() => {
  return buildQuoteAmountSnapshot({
    recyclerQuoteAmount: Number(price.value || 0)
  })
})

const myQuote = computed(() => {
  if (!inquiry.value) return null

  const quotes = Array.isArray(inquiry.value.quotes) ? inquiry.value.quotes : []

  return quotes.find(item => {
    return Number(item.recyclerCompanyId) === Number(currentUser.value.company_id) &&
      Number(item.quoteUserId) === Number(currentUser.value.id)
  })
})

const finishedText = computed(() => {
  if (!inquiry.value) return ''

  if (isOffShelf(inquiry.value)) {
    return '商家已下架该询价单，不能继续报价。'
  }

  if (isAcceptedByMe(inquiry.value)) {
    return '商家已确认你所在回收商的报价，该询价单已进入订单流程。'
  }

  if (isAcceptedByOther(inquiry.value)) {
    return '商家已选择其他回收商成交，你不能继续报价。'
  }

  return '该询价单已结束。'
})

const canSubmit = computed(() => {
  if (!inquiry.value) return false

  if (!canQuoteByFund.value) return false

  if (isFinishedForRecycler(inquiry.value)) return false

  if (!canRoleQuote()) return false

  if (amountNumber.value <= 0) return false

  if (overBalance.value) return false

  if (myQuote.value && !updateReason.value.trim()) return false

  return true
})

function loadData() {
  const list = uni.getStorageSync('inquiryList') || []

  inquiryList.value = list.map(item => {
    return {
      ...item,
      quotes: Array.isArray(item.quotes) ? item.quotes : []
    }
  })

  fundList.value = uni.getStorageSync(FUND_KEY) || []

  ensureCompanyFund()
}

function initForm() {
  // loadData() 已同步填充 inquiryList，myQuote 计算属性此时即可用，无需 setTimeout 兜底
  if (!myQuote.value) return

  price.value = String(myQuote.value.recyclerQuoteAmount || myQuote.value.amount || '')
  validDays.value = myQuote.value.validDays || ''
  remark.value = myQuote.value.remark || ''
}

function saveInquiryList() {
  uni.setStorageSync('inquiryList', inquiryList.value)
}

function saveFundList() {
  uni.setStorageSync(FUND_KEY, fundList.value)
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

function canRoleQuote() {
  return currentUser.value.role === 'recycler_staff' ||
    currentUser.value.role === 'recycler_owner'
}

function submitQuote() {
  if (!canRoleQuote()) {
    uni.showToast({
      title: '当前账号无报价权限',
      icon: 'none'
    })
    return
  }

  if (!canQuoteByFund.value) {
    uni.showModal({
      title: '预付款额度不足',
      content: `当前可用额度低于 ${MIN_QUOTE_FUND} 元，暂不可报价。请先提交预付款凭证并等待平台审核通过。`,
      confirmText: '去提交',
      cancelText: '取消',
      confirmColor: '#4b5563',
      success: res => {
        if (res.confirm) {
          goFundPage()
        }
      }
    })
    return
  }

  if (!price.value) {
    uni.showToast({
      title: '请输入报价金额',
      icon: 'none'
    })
    return
  }

  const amount = Number(price.value)
  const balance = Number(companyFund.value.balance || 0)

  if (!amount || amount <= 0) {
    uni.showToast({
      title: '报价金额不正确',
      icon: 'none'
    })
    return
  }

  if (amount > balance) {
    uni.showModal({
      title: '报价金额超出可用额度',
      content: `当前可用额度为 ¥${formatMoney(balance)}，报价金额不能超过可用额度。`,
      showCancel: false,
      confirmColor: '#4b5563'
    })
    return
  }

  if (myQuote.value && !updateReason.value.trim()) {
    uni.showToast({
      title: '请填写修改原因',
      icon: 'none'
    })
    return
  }

  const target = inquiryList.value.find(item => Number(item.id) === Number(inquiryId.value))

  if (!target) {
    uni.showToast({
      title: '询价单不存在',
      icon: 'none'
    })
    return
  }

  if (isFinishedForRecycler(target)) {
    uni.showToast({
      title: '该询价单已结束',
      icon: 'none'
    })
    return
  }

  if (!Array.isArray(target.quotes)) {
    target.quotes = []
  }

  const amountSnapshot = buildQuoteAmountSnapshot({
    recyclerQuoteAmount: amount
  })

  const oldQuote = target.quotes.find(item => {
    return Number(item.recyclerCompanyId) === Number(currentUser.value.company_id) &&
      Number(item.quoteUserId) === Number(currentUser.value.id)
  })

  if (oldQuote) {
    oldQuote.amount = amountSnapshot.recyclerQuoteAmount
    oldQuote.recyclerQuoteAmount = amountSnapshot.recyclerQuoteAmount

    oldQuote.platformFeeRate = amountSnapshot.platformFeeRate
    oldQuote.platformFeeAmount = amountSnapshot.platformFeeAmount

    oldQuote.merchantBaseAmount = amountSnapshot.merchantBaseAmount
    oldQuote.merchantTip = amountSnapshot.merchantTip

    oldQuote.validDays = validDays.value
    oldQuote.remark = remark.value

    oldQuote.updateReason = updateReason.value
    oldQuote.updateTime = getNowText()
  } else {
    target.quotes.push({
      id: Date.now(),

      recyclerCompanyId: currentUser.value.company_id,
      recyclerCompanyName: currentUser.value.company_name || `中晨回收${currentUser.value.company_id}`,

      quoteUserId: currentUser.value.id,
      quoteUserName: currentUser.value.username,

      amount: amountSnapshot.recyclerQuoteAmount,
      recyclerQuoteAmount: amountSnapshot.recyclerQuoteAmount,

      platformFeeRate: amountSnapshot.platformFeeRate,
      platformFeeAmount: amountSnapshot.platformFeeAmount,

      merchantBaseAmount: amountSnapshot.merchantBaseAmount,
      merchantTip: amountSnapshot.merchantTip,

      validDays: validDays.value,
      remark: remark.value,

      quoteTime: getNowText(),
      updateReason: '',
      updateTime: ''
    })
  }

  target.status = '已有回收商报价'
  target.quoteStatus = 'quoted'

  saveInquiryList()

  uni.showToast({
    title: oldQuote ? '报价已修改' : '报价成功',
    icon: 'success'
  })

  setTimeout(() => {
    uni.navigateBack()
  }, 600)
}

function isOffShelf(item) {
  return item.status === '商家已下架' || item.quoteStatus === 'off_shelf'
}

function isAccepted(item) {
  return item.status === '商家已接单' || item.quoteStatus === 'accepted'
}

function isAcceptedByMe(item) {
  return isAccepted(item) &&
    Number(item.selectedRecyclerCompanyId) === Number(currentUser.value.company_id)
}

function isAcceptedByOther(item) {
  return isAccepted(item) &&
    item.selectedRecyclerCompanyId &&
    Number(item.selectedRecyclerCompanyId) !== Number(currentUser.value.company_id)
}

function isFinishedForRecycler(item) {
  return isOffShelf(item) || isAcceptedByMe(item) || isAcceptedByOther(item)
}

function goFundPage() {
  uni.navigateTo({
    url: '/pages/recycler/settlement/settlement'
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

.quota-card {
  margin-top: 30rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quota-label {
  font-size: 25rpx;
  opacity: 0.9;
}

.quota-money {
  margin-top: 8rpx;
  font-size: 50rpx;
  font-weight: 600;
}

.quota-status {
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: #ffffff;
  font-size: 24rpx;
  font-weight: bold;
}

.quota-status.safe {
  color: #18a058;
}

.quota-status.danger {
  color: #ff5a3c;
}

.warning-card {
  margin: 0 24rpx 24rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  background: #fff0eb;
  color: #ff5a3c;
}

.warning-card.gray {
  background: #eef2f7;
  color: #667085;
}

.warning-title {
  font-size: 30rpx;
  font-weight: 600;
}

.warning-desc {
  margin-top: 12rpx;
  font-size: 25rpx;
  line-height: 38rpx;
}

.warning-btn {
  margin-top: 20rpx;
  height: 74rpx;
  line-height: 74rpx;
  border-radius: 999rpx;
  background: #ff5a3c;
  color: #ffffff;
  font-size: 27rpx;
  font-weight: bold;
}

.warning-btn::after {
  border: none;
}

.card,
.rule-card {
  margin: 0 24rpx 24rpx;
  padding: 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.section-title {
  color: #222222;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 18rpx;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #edf1f5;
  color: #666666;
  font-size: 25rpx;
}

.row text:last-child {
  text-align: right;
  color: #222222;
  font-weight: bold;
}

.form-item {
  margin-top: 26rpx;
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

.textarea {
  width: 100%;
  min-height: 150rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f5f8fb;
  font-size: 28rpx;
  box-sizing: border-box;
}

.old-quote-box {
  padding: 24rpx;
  border-radius: 24rpx;
  background: #f6f7f9;
}

.old-quote-title {
  color: #64748b;
  font-size: 24rpx;
}

.old-quote-money {
  margin-top: 8rpx;
  color: #ff5a3c;
  font-size: 44rpx;
  font-weight: 600;
}

.old-quote-desc {
  margin-top: 8rpx;
  color: #999999;
  font-size: 24rpx;
}

.calc-card {
  margin-top: 22rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f6f7f9;
}

.calc-row {
  display: flex;
  justify-content: space-between;
  color: #222222;
  font-size: 26rpx;
  font-weight: bold;
}

.calc-tip {
  margin-top: 10rpx;
  color: #64748b;
  font-size: 24rpx;
}

.calc-warn {
  margin-top: 14rpx;
  padding: 12rpx 16rpx;
  border-radius: 14rpx;
  background: #fff0eb;
  color: #ff5a3c;
  font-size: 24rpx;
  line-height: 34rpx;
}

.rule-title {
  color: #d97706;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 12rpx;
}

.rule-line {
  color: #9a6200;
  font-size: 24rpx;
  line-height: 40rpx;
}

.rule-card {
  background: #fff7e6;
}

.btn {
  margin: 10rpx 24rpx 0;
  height: 86rpx;
  line-height: 86rpx;
  border-radius: 999rpx;
  background: #17324d;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: bold;
}

.btn[disabled] {
  background: #d5dce3;
  color: #ffffff;
}

.btn::after {
  border: none;
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
