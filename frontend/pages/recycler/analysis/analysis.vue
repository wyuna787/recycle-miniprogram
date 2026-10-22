<template>
  <view class="page">
    <custom-navbar title="数据分析" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ scopeLabel }}</view>
          <view class="title">成交与资金分析</view>
          <view class="desc">
            {{ isStaff ? '仅统计你提交的报价与成交。' : '汇总公司全部报价、成交与资金池数据。' }}
          </view>
        </view>
        <view class="hero-icon">析</view>
      </view>

      <view class="fee-card">
        <view class="fee-label">报价成功率</view>
        <view class="fee-money">{{ successRate }}%</view>
        <view class="fee-sub">报价 {{ quoteCount }} 次 · 成交 {{ dealCount }} 单</view>
      </view>
    </view>

    <view class="grid">
      <view class="grid-item">
        <view class="grid-num">{{ dealCount }}</view>
        <view class="grid-label">成交订单</view>
      </view>
      <view class="grid-item">
        <view class="grid-num">¥{{ formatMoney(totalDealAmount) }}</view>
        <view class="grid-label">成交总额</view>
      </view>
      <view class="grid-item">
        <view class="grid-num">¥{{ formatMoney(fund.deductedAmount) }}</view>
        <view class="grid-label">累计扣款</view>
      </view>
      <view class="grid-item">
        <view class="grid-num">¥{{ formatMoney(fund.frozenAmount) }}</view>
        <view class="grid-label">冻结中</view>
      </view>
    </view>

    <view v-if="!isStaff" class="section">
      <view class="section-title">资金池</view>
      <view class="stat-row">
        <text class="stat-name">总余额</text>
        <text class="stat-amount">¥{{ formatMoney(fund.balance) }}</text>
      </view>
      <view class="stat-row">
        <text class="stat-name">冻结中</text>
        <text class="stat-amount">¥{{ formatMoney(fund.frozenAmount) }}</text>
      </view>
      <view class="stat-row">
        <text class="stat-name">累计扣款</text>
        <text class="stat-amount">¥{{ formatMoney(fund.deductedAmount) }}</text>
      </view>
      <view class="stat-row total">
        <text class="stat-name">可用余额</text>
        <text class="stat-amount pos">¥{{ formatMoney(fund.availableAmount) }}</text>
      </view>
    </view>

    <view v-if="!isStaff" class="section">
      <view class="section-title">员工业绩</view>
      <view v-if="staffRows.length === 0" class="empty-inline">暂无员工报价数据</view>
      <view
        v-for="row in staffRows"
        :key="row.userId"
        class="staff-row"
      >
        <view>
          <view class="staff-name">{{ row.name }}</view>
          <view class="staff-sub">报价 {{ row.quoteCount }} 次 · 成交 {{ row.dealCount }} 单 · 成功率 {{ row.rate }}%</view>
        </view>
        <view class="staff-amount">¥{{ formatMoney(row.dealAmount) }}</view>
      </view>
    </view>

    <view v-else class="section">
      <view class="section-title">我的业绩</view>
      <view class="stat-row">
        <text class="stat-name">我的报价</text>
        <text class="stat-amount">{{ quoteCount }} 次</text>
      </view>
      <view class="stat-row">
        <text class="stat-name">我的成交</text>
        <text class="stat-amount">{{ dealCount }} 单</text>
      </view>
      <view class="stat-row">
        <text class="stat-name">我的成交总额</text>
        <text class="stat-amount pos">¥{{ formatMoney(totalDealAmount) }}</text>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { formatMoney } from '@/utils/moneyMock.js'
import { loadInquiryList, isOrderTrade } from '@/utils/tradeFlow.js'
import { getFund } from '@/utils/fundFlow.js'
import { guardPage } from '@/utils/permission.js'
import { getFundPool } from '@/api/fund.js'
import { getMyQuotes, getMyOrders } from '@/api/trade.js'

const currentUser = ref({})
const myQuotes = ref([])
const myOrders = ref([])
const fund = ref({ balance: 0, frozenAmount: 0, deductedAmount: 0, availableAmount: 0 })

const isStaff = computed(() => currentUser.value.role === 'recycler_staff')

const scopeLabel = computed(() => {
  const map = {
    recycler_owner: '回收商老板',
    recycler_keeper: '回收商库管',
    recycler_staff: '回收商员工'
  }
  return map[currentUser.value.role] || '回收商'
})

onShow(() => {
  currentUser.value = uni.getStorageSync('userInfo') || uni.getStorageSync('currentUser') || {}

  if (!guardPage(currentUser.value, '/pages/recycler/analysis/analysis')) return

  loadData()
})

async function loadData() {
  const cid = Number(currentUser.value.company_id)

  try {
    const [poolRes, quoteRes, orderRes] = await Promise.all([
      getFundPool(cid),
      getMyQuotes(),
      getMyOrders()
    ])

    fund.value = {
      balance: Number(poolRes.balance || 0),
      frozenAmount: Number(poolRes.frozen_amount || 0),
      deductedAmount: Number(poolRes.deducted_amount || 0),
      availableAmount: Number(poolRes.available_amount != null
        ? poolRes.available_amount
        : Number(poolRes.balance || 0) - Number(poolRes.frozen_amount || 0))
    }

    myQuotes.value = quoteRes.list || []
    myOrders.value = orderRes.list || []
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  fund.value = getFund(cid)
  const list = loadInquiryList() || []
  myQuotes.value = []
  myOrders.value = list.filter(item => isOrderTrade(item))
}

// 本人/本公司报价总次数（/api/quotes/my 已按当前账号返回）
const quoteCount = computed(() => myQuotes.value.length)

// 成交订单 = 当前账号可见订单（老板看公司、员工看本人，后端已按角色返回）
const deals = computed(() => myOrders.value)

const dealCount = computed(() => deals.value.length)

const totalDealAmount = computed(() => {
  return deals.value.reduce((s, i) => s + Number(i.price || i.selectedRecyclerQuoteAmount || 0), 0)
})

const successRate = computed(() => {
  if (quoteCount.value === 0) return 0
  return Math.round((dealCount.value / quoteCount.value) * 100)
})

// 按报价员工聚合(老板/库管视角)
const staffRows = computed(() => {
  const map = {}

  function ensure(userId, name) {
    if (!map[userId]) {
      map[userId] = {
        userId,
        name: name || `员工 #${userId || '-'}`,
        quoteCount: 0,
        dealCount: 0,
        dealAmount: 0
      }
    }
    return map[userId]
  }

  myQuotes.value.forEach(q => {
    ensure(Number(q.quoteUserId || q.recycler_id || 0), q.quoteUserName).quoteCount += 1
  })

  deals.value.forEach(order => {
    const row = ensure(Number(order.recycler_id || 0), order.recycler_name)
    row.dealCount += 1
    row.dealAmount += Number(order.price || 0)
  })

  return Object.values(map)
    .map(row => ({
      ...row,
      rate: row.quoteCount ? Math.round((row.dealCount / row.quoteCount) * 100) : 0
    }))
    .sort((a, b) => b.dealAmount - a.dealAmount)
})
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
  border-bottom: 1rpx solid #eef1f4;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row.total {
  margin-top: 4rpx;
  border-top: 2rpx solid #eef1f4;
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

.stat-amount.pos {
  color: #18a058;
}

.staff-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #eef1f4;
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
  color: #374151;
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
