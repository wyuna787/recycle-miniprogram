<template>
  <view class="page">
    <custom-navbar title="数据分析" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ isOwner ? '商家老板' : '商家员工' }}</view>
          <view class="title">成交与抽成分析</view>
          <view class="desc">
            {{ isOwner ? '汇总公司全部成交订单的金额与抽成。' : '仅统计你参与的成交订单。' }}
          </view>
        </view>
        <view class="hero-icon">析</view>
      </view>

      <view class="fee-card">
        <view class="fee-label">真实成交总额</view>
        <view class="fee-money">¥{{ formatMoney(totalRealAmount) }}</view>
        <view class="fee-sub">展示总额 ¥{{ totalDisplayAmount }}（工作台口径，已去小数）</view>
      </view>
    </view>

    <view class="grid">
      <view class="grid-item">
        <view class="grid-num">{{ dealCount }}</view>
        <view class="grid-label">成交订单</view>
      </view>
      <view class="grid-item">
        <view class="grid-num">¥{{ formatMoney(totalOwnerCommission) }}</view>
        <view class="grid-label">老板抽成</view>
      </view>
      <view class="grid-item">
        <view class="grid-num">¥{{ formatMoney(totalStaffCommission) }}</view>
        <view class="grid-label">员工抽成</view>
      </view>
    </view>

    <view v-if="pendingDealCount > 0" class="hint-card">
      还有 {{ pendingDealCount }} 单进行中，抽成将在回收商确认收货、订单完成后结算计入。
    </view>

    <view class="section">
      <view class="section-title">金额构成（已完成订单）</view>
      <view class="stat-row total">
        <text class="stat-name">真实成交金额</text>
        <text class="stat-amount pos">¥{{ formatMoney(totalRealAmount) }}</text>
      </view>
      <view class="stat-row">
        <text class="stat-name">老板抽成</text>
        <text class="stat-amount">¥{{ formatMoney(totalOwnerCommission) }}</text>
      </view>
      <view class="stat-row">
        <text class="stat-name">员工抽成</text>
        <text class="stat-amount">¥{{ formatMoney(totalStaffCommission) }}</text>
      </view>
    </view>

    <view v-if="isOwner" class="section">
      <view class="section-title">员工业绩</view>
      <view v-if="staffRows.length === 0" class="empty-inline">暂无员工成交数据</view>
      <view
        v-for="row in staffRows"
        :key="row.userId"
        class="staff-row"
      >
        <view>
          <view class="staff-name">{{ row.name }}</view>
          <view class="staff-sub">成交 {{ row.count }} 单 · 员工抽成 ¥{{ formatMoney(row.staffCommission) }}</view>
        </view>
        <view class="staff-amount">¥{{ formatMoney(row.realAmount) }}</view>
      </view>
    </view>

    <view v-else class="section">
      <view class="section-title">我的业绩</view>
      <view class="stat-row">
        <text class="stat-name">我的成交单数</text>
        <text class="stat-amount">{{ dealCount }} 单</text>
      </view>
      <view class="stat-row">
        <text class="stat-name">我的员工抽成</text>
        <text class="stat-amount pos">¥{{ formatMoney(totalStaffCommission) }}</text>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { formatMoney, formatDisplayMoney } from '@/utils/moneyMock.js'
import { loadInquiryList, isOrderTrade, isTradeStatus, TRADE_STATUS } from '@/utils/tradeFlow.js'
import { guardPage } from '@/utils/permission.js'
import { getMyOrders } from '@/api/trade.js'

const currentUser = ref({})
const orderList = ref([])

const isOwner = computed(() => currentUser.value.role === 'merchant_owner')

onShow(async () => {
  currentUser.value = uni.getStorageSync('currentUser') || uni.getStorageSync('userInfo') || {}

  if (!guardPage(currentUser.value, '/pages/merchant/analysis/analysis')) return

  try {
    const res = await getMyOrders()
    orderList.value = (res.list || []).map(mapApiOrder)
    return
  } catch (error) {
    orderList.value = []; return // 加载失败不得显示其他账号的旧数据
  }

  orderList.value = loadInquiryList() || []
})

function mapApiOrder(order) {
  return {
    ...order,
    tradeStatus: order.status,
    merchantCompanyId: order.merchant?.company_id ?? order.merchant_company_id,
    merchantUserId: order.merchant_id
  }
}

// 抽成只在订单全部结束(回收商确认收货、订单完成)后才计入结算
function isSettledDeal(item) {
  return item.fund_status === 'deducted' || isTradeStatus(item, TRADE_STATUS.COMPLETED, 'platform_paid') ||
    item.status === '交易完成' ||
    item.status === 'completed'
}

// 本人/本公司可见、且已完成结算的成交订单
const deals = computed(() => {
  const user = currentUser.value

  return orderList.value.filter(item => {
    if (!isOrderTrade(item) && !isSettledDeal(item)) return false
    if (!isSettledDeal(item)) return false

    if (user.role === 'merchant_owner') {
      return Number(item.merchantCompanyId) === Number(user.company_id) ||
        Number(item.company_id) === Number(user.company_id)
    }

    if (user.role === 'merchant_staff') {
      return Number(item.merchantUserId) === Number(user.id) ||
        Number(item.merchant_id) === Number(user.id)
    }

    return false
  })
})

// 进行中(未结算)的订单数：用于提示「抽成在订单完成后结算」
const pendingDealCount = computed(() => {
  const user = currentUser.value

  return orderList.value.filter(item => {
    if (!isOrderTrade(item)) return false
    if (isSettledDeal(item)) return false

    if (user.role === 'merchant_owner') {
      return Number(item.merchantCompanyId) === Number(user.company_id) ||
        Number(item.company_id) === Number(user.company_id)
    }

    return Number(item.merchantUserId) === Number(user.id) ||
      Number(item.merchant_id) === Number(user.id)
  }).length
})

const dealCount = computed(() => deals.value.length)

function sumBy(field) {
  return deals.value.reduce((s, i) => s + Number(i[field] || 0), 0)
}

const totalMerchantBase = computed(() => sumBy('selectedMerchantBaseAmount'))
const totalOwnerCommission = computed(() => sumBy('selectedMerchantOwnerCommission'))
const totalStaffCommission = computed(() => sumBy('selectedMerchantStaffCommission'))
const totalRealAmount = computed(() => sumBy('selectedMerchantRealAmount'))
const totalDisplayAmount = computed(() => formatDisplayMoney(totalRealAmount.value))

// 按员工聚合(老板视角)
const staffRows = computed(() => {
  const map = {}

  deals.value.forEach(item => {
    const userId = Number(item.merchantUserId || item.merchant_id || 0)
    if (!map[userId]) {
      map[userId] = {
        userId,
        name: userId === Number(currentUser.value.id)
          ? `${currentUser.value.name || '我'}（我）`
          : `员工 #${userId || '-'}`,
        count: 0,
        realAmount: 0,
        staffCommission: 0
      }
    }

    map[userId].count += 1
    map[userId].realAmount += Number(item.selectedMerchantRealAmount || 0)
    map[userId].staffCommission += Number(item.selectedMerchantStaffCommission || 0)
  })

  return Object.values(map).sort((a, b) => b.realAmount - a.realAmount)
})
</script>





<style scoped>

.page {
  min-height: 100vh;
  background: #fff6ec;
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

.fee-card {
  margin-top: 30rpx;
  padding: 26rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.2);
}

.fee-label {
  font-size: 24rpx;
  opacity: 0.9;
}

.fee-money {
  margin-top: 8rpx;
  font-size: 50rpx;
  font-weight: 600;
}

.fee-sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  opacity: 0.9;
}

.grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin: 0 24rpx 8rpx;
}

.grid-item {
  width: calc(50% - 8rpx);
  padding: 26rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
  box-sizing: border-box;
}

.grid-num {
  color: #111111;
  font-size: 38rpx;
  font-weight: 600;
}

.grid-label {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.hint-card {
  margin: 0 24rpx 4rpx;
  padding: 22rpx 26rpx;
  border-radius: 22rpx;
  background: #fff3e0;
  color: #d97706;
  font-size: 24rpx;
  line-height: 36rpx;
}

.section {
  margin: 24rpx;
  padding: 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.section-title {
  margin-bottom: 18rpx;
  color: #222222;
  font-size: 32rpx;
  font-weight: 600;
}

.stat-row {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f1eee9;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row.total {
  margin-top: 4rpx;
  border-top: 2rpx solid #f1eee9;
  border-bottom: none;
}

.stat-name {
  flex: 1;
  color: #333333;
  font-size: 26rpx;
  font-weight: bold;
}

.stat-amount {
  color: #222222;
  font-size: 27rpx;
  font-weight: 600;
}

.stat-amount.neg {
  color: #d4380d;
}

.stat-amount.pos {
  color: #18a058;
}

.staff-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #f1eee9;
}

.staff-row:last-child {
  border-bottom: none;
}

.staff-name {
  color: #222222;
  font-size: 27rpx;
  font-weight: bold;
}

.staff-sub {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 24rpx;
}

.staff-amount {
  color: #ff8a3d;
  font-size: 26rpx;
  font-weight: 600;
}

.empty-inline {
  padding: 30rpx;
  text-align: center;
  color: #64748b;
  font-size: 25rpx;
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
