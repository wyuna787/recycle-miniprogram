<template>
  <view class="page">
    <custom-navbar title="数据总览" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">平台管理员</view>
          <view class="title">资金总览</view>
          <view class="desc">
            汇总平台收入、各回收商资金池与资金流水，仅做数字统计。
          </view>
        </view>

        <view class="hero-icon">览</view>
      </view>

      <view class="fee-card">
        <view class="fee-label">平台累计收入</view>
        <view class="fee-money">¥{{ formatMoney(platformFeeTotal) }}</view>
      </view>
    </view>

    <view class="grid">
      <view class="grid-item">
        <view class="grid-num">¥{{ formatMoney(totalBalance) }}</view>
        <view class="grid-label">资金池总余额</view>
      </view>
      <view class="grid-item">
        <view class="grid-num">¥{{ formatMoney(totalFrozen) }}</view>
        <view class="grid-label">冻结中</view>
      </view>
      <view class="grid-item">
        <view class="grid-num">¥{{ formatMoney(totalDeducted) }}</view>
        <view class="grid-label">累计扣款</view>
      </view>
      <view class="grid-item">
        <view class="grid-num">{{ dealCount }}</view>
        <view class="grid-label">成交订单</view>
      </view>
    </view>

    <view class="section">
      <view class="section-title">各回收商资金池</view>

      <view v-if="funds.length === 0" class="empty-inline">暂无回收商资金池</view>

      <view
        v-for="row in funds"
        :key="row.companyId"
        class="fund-row"
      >
        <view>
          <view class="fund-name">{{ row.companyName }}</view>
          <view class="fund-sub">冻结 ¥{{ formatMoney(row.frozenAmount) }} · 已扣 ¥{{ formatMoney(row.deductedAmount) }}</view>
        </view>
        <view class="fund-avail">可用 ¥{{ formatMoney(row.balance - row.frozenAmount) }}</view>
      </view>
    </view>

    <view class="section">
      <view class="section-title">资金流水汇总</view>

      <view
        v-for="stat in flowStats"
        :key="stat.type"
        class="stat-row"
      >
        <text class="stat-name">{{ stat.label }}</text>
        <text class="stat-meta">{{ stat.count }} 笔</text>
        <text class="stat-amount">¥{{ formatMoney(stat.amount) }}</text>
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
import { loadFunds, loadFlows, getFlowTypeText, FLOW_TYPE } from '@/utils/fundFlow.js'
import { guardPage } from '@/utils/permission.js'
import { getAdminFundPools, getAdminFundFlows } from '@/api/fund.js'
import { getAdminTrades } from '@/api/trade.js'

const currentUser = ref({})
const funds = ref([])
const flows = ref([])
const orderList = ref([])

onShow(() => {
  currentUser.value = uni.getStorageSync('userInfo') || uni.getStorageSync('currentUser') || {}

  if (!guardPage(currentUser.value, '/pages/platform/dashboard/dashboard')) return

  loadData()
})

async function loadData() {
  try {
    const [poolRes, flowRes, tradeRes] = await Promise.all([
      getAdminFundPools(),
      getAdminFundFlows(),
      getAdminTrades()
    ])

    funds.value = (poolRes.list || []).map(item => ({
      companyId: Number(item.company_id),
      companyName: item.company_name || `回收商${item.company_id}`,
      balance: Number(item.balance || 0),
      frozenAmount: Number(item.frozen_amount || 0),
      deductedAmount: Number(item.deducted_amount || 0)
    }))

    flows.value = (flowRes.list || []).map(item => ({
      id: item.id,
      type: item.type,
      companyId: Number(item.company_id),
      amount: Number(item.amount || 0)
    }))

    // 仅统计已生成订单的成交，pending/quoted 询价不计入
    orderList.value = (tradeRes.list || [])
      .filter(item => item.orderId || item.order)
      .map(item => ({ ...item, tradeStatus: item.tradeStatus || 'order' }))
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  funds.value = (loadFunds() || []).map(item => ({
    companyId: Number(item.companyId),
    companyName: item.companyName || `回收商${item.companyId}`,
    balance: Number(item.balance || 0),
    frozenAmount: Number(item.frozenAmount || 0),
    deductedAmount: Number(item.deductedAmount || 0)
  }))

  flows.value = loadFlows() || []
  orderList.value = loadInquiryList() || []
}

const totalBalance = computed(() => funds.value.reduce((s, i) => s + i.balance, 0))
const totalFrozen = computed(() => funds.value.reduce((s, i) => s + i.frozenAmount, 0))
const totalDeducted = computed(() => funds.value.reduce((s, i) => s + i.deductedAmount, 0))

const platformFeeTotal = computed(() => {
  return flows.value
    .filter(item => item.type === FLOW_TYPE.PLATFORM_FEE)
    .reduce((s, i) => s + Number(i.amount || 0), 0)
})

const dealCount = computed(() => {
  return orderList.value.filter(item => isOrderTrade(item)).length
})

// 按流水类型汇总笔数与金额
const flowStats = computed(() => {
  const types = [
    FLOW_TYPE.RECHARGE,
    FLOW_TYPE.FREEZE,
    FLOW_TYPE.DEDUCT,
    FLOW_TYPE.RELEASE,
    FLOW_TYPE.PLATFORM_FEE
  ]

  return types.map(type => {
    const rows = flows.value.filter(item => item.type === type)
    return {
      type,
      label: getFlowTypeText(type),
      count: rows.length,
      amount: rows.reduce((s, i) => s + Number(i.amount || 0), 0)
    }
  })
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

.fund-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #eef1f4;
}

.fund-row:last-child {
  border-bottom: none;
}

.fund-name {
  color: #222222;
  font-size: 27rpx;
  font-weight: bold;
}

.fund-sub {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 24rpx;
}

.fund-avail {
  color: #18a058;
  font-size: 26rpx;
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

.stat-name {
  flex: 1;
  color: #333333;
  font-size: 26rpx;
  font-weight: bold;
}

.stat-meta {
  margin-right: 20rpx;
  color: #64748b;
  font-size: 24rpx;
}

.stat-amount {
  color: #222222;
  font-size: 27rpx;
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
