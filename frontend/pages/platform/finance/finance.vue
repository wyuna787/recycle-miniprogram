<template>
  <view class="page">
    <custom-navbar title="财务流水明细" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">平台管理员</view>
          <view class="title">财务流水明细</view>
          <view class="desc">逐条查看充值、冻结、释放、扣款与平台收入记录。</view>
        </view>
        <view class="hero-icon">流</view>
      </view>

      <view class="sum-card">
        <view class="sum-col">
          <view class="sum-num">{{ filteredFlows.length }}</view>
          <view class="sum-label">当前笔数</view>
        </view>
        <view class="sum-col">
          <view class="sum-num">¥{{ formatMoney(filteredTotal) }}</view>
          <view class="sum-label">当前金额合计</view>
        </view>
      </view>
    </view>

    <scroll-view scroll-x class="filter-bar">
      <view
        v-for="tab in typeTabs"
        :key="tab.value"
        :class="['filter-chip', activeType === tab.value ? 'active' : '']"
        @click="activeType = tab.value"
      >
        {{ tab.label }}
      </view>
    </scroll-view>

    <view class="section">
      <input class="order-search" v-model="flowSearch" placeholder="订单号 / 公司ID / 公司名称" />
      <view>开始时间<input class="order-search" v-model="startTime" placeholder="2026-10-11 00:00:00" /></view>
      <view>结束时间<input class="order-search" v-model="endTime" placeholder="2026-10-11 23:59:59" /></view>
      <view class="filter-bar"><text @click="flowKind='all'">全部</text>　<text @click="flowKind='recycler'">回收商</text>　<text @click="flowKind='merchant'">商家</text></view>
      <view v-if="filteredFlows.length === 0" class="empty-inline">暂无流水记录</view>

      <view
        v-for="flow in filteredFlows"
        :key="flow.id"
        class="flow-row"
      >
        <view class="flow-left">
          <view class="flow-head">
            <text :class="['flow-tag', tagClass(flow.type)]">{{ getFlowTypeText(flow.type) }}</text>
            <text class="flow-company">{{ companyName(flow.companyId,flow.companyType) }}</text>
          </view>
          <view class="flow-meta">{{ flow.orderNo ? '订单 ' + flow.orderNo + ' · ' : '' }}{{ flow.time }}</view>
          <view v-if="flow.remark" class="flow-remark">{{ flow.remark }}</view>
        </view>

        <view :class="['flow-amount', amountClass(flow)]">
          {{ amountPrefix(flow) }}¥{{ formatMoney(Math.abs(flow.amount)) }}
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
import { loadFlows, loadFunds, getFlowTypeText, FLOW_TYPE } from '@/utils/fundFlow.js'
import { guardPage } from '@/utils/permission.js'
import { getAdminFundFlows, getAdminFundPools } from '@/api/fund.js'

const currentUser = ref({})
const flows = ref([])
const funds = ref([])
const activeType = ref('all')
const flowSearch=ref(''),startTime=ref(''),endTime=ref(''),flowKind=ref('all')

const typeTabs = [
  { value: 'all', label: '全部' },
  { value: FLOW_TYPE.RECHARGE, label: '充值入账' },
  { value: FLOW_TYPE.FREEZE, label: '报价冻结' },
  { value: FLOW_TYPE.RELEASE, label: '释放冻结' },
  { value: FLOW_TYPE.DEDUCT, label: '成交扣款' },
  { value: FLOW_TYPE.PLATFORM_FEE, label: '平台收入' },
  {value:'manual_deduct',label:'人工扣除'},
  {value:'merchant_recharge',label:'商家充值'},
  {value:'merchant_refund',label:'商家退款'}
]

onShow(() => {
  currentUser.value = uni.getStorageSync('userInfo') || uni.getStorageSync('currentUser') || {}

  if (!guardPage(currentUser.value, '/pages/platform/finance/finance')) return

  loadData()
})

async function loadData() {
  try {
    const [flowRes, poolRes] = await Promise.all([
      getAdminFundFlows(),
      getAdminFundPools()
    ])

    flows.value = (flowRes.list || []).map(item => ({
      id: item.id,
      type: item.type,
      companyId: Number(item.company_id),
      companyType:item.company_type || 'recycler',
      companyName:item.company_name || '',
      amount: Number(item.amount || 0),
      time: item.create_time || '',
      orderNo: item.order_no || '',
      remark: item.remark || ''
    }))

    funds.value = (poolRes.list || []).map(item => ({
      companyId: Number(item.company_id),
      companyName: item.company_name || `回收商${item.company_id}`,
      balance: Number(item.balance || 0),
      frozenAmount: Number(item.frozen_amount || 0),
      deductedAmount: Number(item.deducted_amount || 0)
    }))
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  flows.value = loadFlows() || []
  funds.value = loadFunds() || []
}

const filteredFlows = computed(() => {
  const term=flowSearch.value.trim().toLowerCase()
  return flows.value.filter(item => (activeType.value==='all'||item.type===activeType.value) &&
    (flowKind.value==='all'||item.companyType===flowKind.value) &&
    (!term||[item.orderNo,item.companyId,item.companyName].some(v=>String(v||'').toLowerCase().includes(term))) &&
    (!startTime.value.trim()||item.time>=startTime.value.trim()) && (!endTime.value.trim()||item.time<=endTime.value.trim()))
})

const filteredTotal = computed(() => {
  return filteredFlows.value.reduce((s, i) => s + Number(i.amount || 0), 0)
})

function companyName(companyId,kind) {
  const flow=flows.value.find(item=>item.companyId===companyId&&item.companyType===kind)
  if(flow?.companyName)return (kind==='merchant'?'商家 · ':'回收商 · ')+flow.companyName

  const fund = funds.value.find(item => Number(item.companyId) === Number(companyId))
  return (fund && fund.companyName) || `回收商${companyId || '-'}`
}

// 释放/充值为入账(绿色 +),冻结/扣款/服务费为占用(红色 -)
function amountClass(flow) {
  return amountPrefix(flow)==='+'?'plus':'minus'
}

function amountPrefix(flow) {
  return flow.amount>=0 && [FLOW_TYPE.RECHARGE,FLOW_TYPE.RELEASE,'merchant_recharge'].includes(flow.type) ? '+' : '-'
}

function tagClass(type) {
  if (type === FLOW_TYPE.RECHARGE) return 'green'
  if (type === FLOW_TYPE.RELEASE) return 'blue'
  if (type === FLOW_TYPE.PLATFORM_FEE) return 'purple'
  return 'orange'
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

.sum-card {
  margin-top: 30rpx;
  padding: 26rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
}

.sum-col {
  flex: 1;
}

.sum-num {
  font-size: 40rpx;
  font-weight: 600;
}

.sum-label {
  margin-top: 6rpx;
  font-size: 24rpx;
  opacity: 0.9;
}

.filter-bar {
  margin: 8rpx 24rpx 0;
  white-space: nowrap;
}

.filter-chip {
  display: inline-block;
  margin-right: 16rpx;
  padding: 12rpx 26rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: #5b6470;
  font-size: 25rpx;
  box-shadow: none;
}

.filter-chip.active {
  background: #374151;
  color: #ffffff;
  font-weight: bold;
}

.section {
  margin: 24rpx;
  padding: 12rpx 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.flow-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #eef1f4;
}

.flow-row:last-child {
  border-bottom: none;
}

.flow-left {
  flex: 1;
  margin-right: 16rpx;
}

.flow-head {
  display: flex;
  align-items: center;
}

.flow-tag {
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
  color: #ffffff;
}

.flow-tag.orange { background: #ff8a3d; }
.flow-tag.green { background: #18a058; }
.flow-tag.blue { background: #374151; }
.flow-tag.purple { background: #8a6bff; }

.flow-company {
  margin-left: 14rpx;
  color: #222222;
  font-size: 26rpx;
  font-weight: bold;
}

.flow-meta {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.flow-remark {
  margin-top: 6rpx;
  color: #b3b8be;
  font-size: 24rpx;
}

.flow-amount {
  font-size: 30rpx;
  font-weight: 600;
}

.flow-amount.plus { color: #18a058; }
.flow-amount.minus { color: #d4380d; }

.empty-inline {
  padding: 40rpx;
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
