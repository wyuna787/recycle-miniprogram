<template>
  <view class="page">
    <custom-navbar title="订单监控" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ currentUser.username || '平台管理员' }}</view>
          <view class="desc">查看全部商家发起的交易主线，含询价、报价与订单。</view>
        </view>
        <view class="hero-icon">单</view>
      </view>

      <view class="stats">
        <view class="stat-item">
          <view class="stat-number">{{ inquiryCount }}</view>
          <view class="stat-label">交易</view>
        </view>
        <view class="stat-item">
          <view class="stat-number">{{ orderCount }}</view>
          <view class="stat-label">订单</view>
        </view>
        <view class="stat-item">
          <view class="stat-number">{{ appealCount }}</view>
          <view class="stat-label">申诉</view>
        </view>
      </view>
    </view>

    <input class="order-search" v-model="orderSearch" placeholder="输入订单号或询价单号" confirm-type="search" />
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

    <view v-if="loading" class="empty">加载中...</view>

    <view v-else-if="displayList.length === 0" class="empty">
      {{ emptyText }}
    </view>

    <view v-for="item in displayList" :key="item.id" class="card">
      <view class="card-head">
        <view>
          <view class="card-title">{{ getDeviceTitle(item) }}</view>
          <view class="card-sub">{{ getOrderNoText(item) }}</view>
        </view>
        <view :class="['status-pill', cardStatus(item).className]">
          {{ cardStatus(item).text }}
        </view>
      </view>

      <view class="detail-entry" @click="openDeviceDetail(item)">
        <text>查看设备详细信息</text>
        <text class="detail-arrow">›</text>
      </view>

      <view class="info-box">
        <view class="info-row">
          <text>商家</text>
          <text>{{ getMerchantText(item) }}</text>
        </view>
        <view class="info-row">
          <text>状态</text>
          <text>{{ getTradeFlowStatusLabel(getTradeStatus(item)) }}</text>
        </view>
        <view class="info-row">
          <text>报价数</text>
          <text>{{ item.quoteCount || 0 }}</text>
        </view>
        <view v-if="item.quoteCount > 0" class="info-row">
          <text>报价区间</text>
          <text>{{ getQuoteRangeText(item) }}</text>
        </view>
        <view class="info-row">
          <text>订单号</text>
          <text>{{ getOrderNoText(item) }}</text>
        </view>
        <view v-if="item.order" class="info-row">
          <text>成交金额</text>
          <text>¥{{ formatAmount(item.order.price || item.selectedAmount) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'inspection_done'" class="info-row">
          <text>验机结果</text>
          <text>{{ getInspectionResultText(getInspectionType(item)) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'inspection_done' && getInspectionPrice(item)" class="info-row">
          <text>调价金额</text>
          <text>¥{{ formatAmount(getInspectionPrice(item)) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'inspection_done' && getInspectionReason(item)" class="info-row">
          <text>验机说明</text>
          <text>{{ getInspectionReason(item) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'inspection_done' && getInspectionTime(item)" class="info-row">
          <text>验机时间</text>
          <text>{{ getInspectionTime(item) }}</text>
        </view>
        <view v-if="item.order && item.receiveTime" class="info-row">
          <text>签收时间</text>
          <text>{{ item.receiveTime }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'completed' && getMerchantConfirmTime(item)" class="info-row">
          <text>商家确认时间</text>
          <text>{{ getMerchantConfirmTime(item) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'appealing' && getAppealReason(item)" class="info-row">
          <text>申诉原因</text>
          <text>{{ getAppealReason(item) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'appealing' && getAppealTime(item)" class="info-row">
          <text>申诉时间</text>
          <text>{{ getAppealTime(item) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'closed' && getCloseReason(item)" class="info-row">
          <text>关闭原因</text>
          <text>{{ getCloseReason(item) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'closed' && getCloseTime(item)" class="info-row">
          <text>关闭时间</text>
          <text>{{ getCloseTime(item) }}</text>
        </view>
        <view v-if="item.order && getTradeStatus(item) === 'shipped'" class="info-row">
          <text>物流</text>
          <text>{{ item.expressCompany || '-' }} {{ item.expressNo || '-' }}</text>
        </view>
        <view v-else-if="item.order && item.expressNo" class="info-row">
          <text>物流</text>
          <text>{{ item.expressCompany || '-' }} {{ item.expressNo }}</text>
        </view>
        <view class="info-row">
          <text>创建时间</text>
          <text>{{ item.createTime || '-' }}</text>
        </view>

        <view v-if="canCloseOrder(item)" class="action-row">
          <button class="close-btn" @click="openClosePopup(item)">关闭订单</button>
        </view>
      </view>
    </view>

    <view v-if="closePopupVisible" class="mask" @click="closeClosePopup">
      <view class="popup" @click.stop>
        <view class="popup-title">关闭订单</view>
        <view class="popup-desc">{{ getDeviceTitle(currentCloseTrade) }}</view>

        <view class="form-item">
          <view class="label">关闭原因</view>
          <textarea
            class="textarea"
            v-model="closeReason"
            placeholder="请填写关闭原因"
          />
        </view>

        <view class="popup-actions">
          <view class="popup-btn cancel" @click="closeClosePopup">取消</view>
          <view class="popup-btn confirm" @click="submitCloseOrder">确认关闭</view>
        </view>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getAdminTrades, getMyOrders, closeAdminOrder } from '@/api/trade.js'
import {
  TRADE_STATUS,
  getAdminTradeStatus,
  getTradeFlowStatusLabel,
  getDeviceTitle,
  getInspectionResultText,
  normalizeAdminTradeList,
  ordersToAdminTradeFallback,
  openDeviceDetail
} from '@/utils/tradeFlow.js'

const currentUser = ref({})
const tradeList = ref([])
const activeTab = ref('inquiry')
const loading = ref(false)

const closePopupVisible = ref(false)
const currentCloseTrade = ref({})
const closeReason = ref('')

onShow(() => {
  currentUser.value = uni.getStorageSync('userInfo') ||
    uni.getStorageSync('currentUser') ||
    {}

  if (currentUser.value.role !== 'platform_admin') {
    uni.showToast({ title: '暂无权限', icon: 'none' })
    uni.reLaunch({ url: '/pages/home/home' })
    return
  }

  loadData()
})

const inquiryCount = computed(() => tradeList.value.length)

const orderCount = computed(() => {
  return tradeList.value.filter(item => !!item.order).length
})

const appealCount = computed(() => {
  return tradeList.value.filter(item => isAppealing(item)).length
})

const inquiryTabList = computed(() => tradeList.value)

const orderTabList = computed(() => {
  return tradeList.value.filter(item => !!item.order)
})

const appealTabList = computed(() => {
  return tradeList.value.filter(item => isAppealing(item))
})

const tabs = computed(() => [
  { key: 'inquiry', name: '询价', badge: inquiryCount.value || '' },
  { key: 'order', name: '订单', badge: orderCount.value || '' },
  { key: 'appeal', name: '申诉', badge: appealCount.value || '' }
])

const orderSearch = ref('')
const displayList = computed(() => {
  const list = activeTab.value === 'order' ? orderTabList.value : activeTab.value === 'appeal' ? appealTabList.value : inquiryTabList.value
  const term = orderSearch.value.trim().toLowerCase()
  return term ? tradeList.value.filter(item => [item.orderNo, item.order?.order_no, item.order?.orderNo, item.no, `XJ${item.id}`].some(value => String(value || '').toLowerCase().includes(term))) : list
})

const emptyText = computed(() => {
  if (activeTab.value === 'appeal') return '暂无申诉交易'
  if (activeTab.value === 'order') return '暂无已生成订单的交易'
  return '暂无商家发起的交易'
})

async function loadData() {
  loading.value = true

  try {
    const res = await getAdminTrades()
    tradeList.value = normalizeAdminTradeList(res)
  } catch (error) {
    try {
      const res = await getMyOrders()
      tradeList.value = ordersToAdminTradeFallback(res)
    } catch (fallbackError) {
      tradeList.value = []
    }
  } finally {
    loading.value = false
  }
}

function getTradeStatus(item) {
  return getAdminTradeStatus(item)
}

function isAppealing(item) {
  const status = getTradeStatus(item)
  return status === TRADE_STATUS.APPEALING || item.order?.status === TRADE_STATUS.APPEALING
}

function getMerchantText(item) {
  const name = item.merchantCompanyName || item.merchant?.company_name || item.merchant?.name || '-'
  const phone = item.merchantPhone || item.merchant?.phone || ''

  return phone ? `${name} / ${phone}` : name
}

function getOrderNoText(item) {
  const orderNo = item.orderNo || item.order?.order_no || item.order?.orderNo || ''
  return orderNo || '暂未生成订单'
}

function getQuoteRangeText(item) {
  const min = item.minQuotePrice
  const max = item.maxQuotePrice

  if (min == null || max == null) return '-'
  if (Number(min) === Number(max)) return `¥${formatAmount(min)}`
  return `¥${formatAmount(min)} ~ ¥${formatAmount(max)}`
}

function formatAmount(value) {
  const num = Number(value || 0)
  return Number.isNaN(num) ? '0.00' : num.toFixed(2)
}

function mapInspectionResult(type) {
  if (type === 'reject') return 'return'
  return type || ''
}

function getInspectionType(item) {
  const order = item.order || {}
  return mapInspectionResult(
    order.inspection_type || order.inspectionType || item.inspection_type || item.inspectionType
  )
}

function getInspectionPrice(item) {
  const order = item.order || {}
  const price = order.inspection_price ?? order.inspectionPrice ?? item.inspection_price ?? item.inspectionPrice
  return price == null || price === '' ? null : price
}

function getInspectionReason(item) {
  const order = item.order || {}
  return order.inspection_reason || order.inspectionReason || item.inspection_reason || item.inspectionReason || ''
}

function getInspectionTime(item) {
  const order = item.order || {}
  return order.inspection_time || order.inspectionTime || item.inspection_time || item.inspectionTime || ''
}

function getOrderField(item, snakeKey, camelKey) {
  const order = item.order || {}
  return order[snakeKey] || order[camelKey] || item[snakeKey] || item[camelKey] || ''
}

function getMerchantConfirmTime(item) {
  return getOrderField(item, 'merchant_confirm_time', 'merchantConfirmTime')
}

function getAppealReason(item) {
  return getOrderField(item, 'appeal_reason', 'appealReason')
}

function getAppealTime(item) {
  return getOrderField(item, 'appeal_time', 'appealTime')
}

function getCloseReason(item) {
  return getOrderField(item, 'close_reason', 'closeReason')
}

function getCloseTime(item) {
  return getOrderField(item, 'close_time', 'closeTime')
}

function getOrderId(item) {
  return item.order?.id || item.order_id || null
}

function canCloseOrder(item) {
  if (!item.order) return false

  const status = getTradeStatus(item)

  return [
    TRADE_STATUS.CONFIRMED,
    TRADE_STATUS.SHIPPED,
    TRADE_STATUS.RECEIVED,
    TRADE_STATUS.INSPECTION_DONE,
    TRADE_STATUS.APPEALING
  ].includes(status)
}

function openClosePopup(item) {
  currentCloseTrade.value = item
  closeReason.value = ''
  closePopupVisible.value = true
}

function closeClosePopup() {
  closePopupVisible.value = false
  currentCloseTrade.value = {}
  closeReason.value = ''
}

async function submitCloseOrder() {
  if (!closeReason.value.trim()) {
    uni.showToast({ title: '请填写关闭原因', icon: 'none' })
    return
  }

  const item = currentCloseTrade.value
  const orderId = getOrderId(item)

  if (!orderId) {
    uni.showToast({ title: '订单不存在', icon: 'none' })
    return
  }

  try {
    await closeAdminOrder(orderId, {
      close_reason: closeReason.value.trim()
    })
    closeClosePopup()
    uni.showToast({ title: '订单已关闭', icon: 'success' })
    await loadData()
    return
  } catch (error) {
    // 回退本地状态
  }

  const target = tradeList.value.find(row => Number(getOrderId(row)) === Number(orderId))

  if (!target || !target.order) return

  const now = new Date()
  const closeTimeText = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  const reason = closeReason.value.trim()

  target.order.status = TRADE_STATUS.CLOSED
  target.order.close_reason = reason
  target.order.closeReason = reason
  target.order.close_time = closeTimeText
  target.order.closeTime = closeTimeText
  target.tradeStatus = TRADE_STATUS.CLOSED
  target.status = TRADE_STATUS.CLOSED
  target.trade_status = TRADE_STATUS.CLOSED

  closeClosePopup()
  uni.showToast({ title: '订单已关闭', icon: 'success' })
}

function cardStatus(item) {
  const status = getTradeStatus(item)
  const text = getTradeFlowStatusLabel(status)

  if (status === TRADE_STATUS.COMPLETED) {
    return { text, className: 'success' }
  }

  if (status === TRADE_STATUS.APPEALING) {
    return { text, className: 'cancel' }
  }

  if (status === TRADE_STATUS.CLOSED) {
    return { text, className: 'off' }
  }

  if (status === 'pending_quote' || status === 'quoted') {
    return { text, className: 'waiting' }
  }

  if (status === TRADE_STATUS.CONFIRMED) {
    return { text, className: 'waiting' }
  }

  if (status === TRADE_STATUS.INSPECTION_DONE) {
    return { text, className: 'processing' }
  }

  return { text, className: 'processing' }
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

.empty {
  margin: 0 24rpx;
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

.detail-entry {
  margin-top: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  border-radius: 18rpx;
  background: #eef0f4;
  color: #17324d;
  font-size: 26rpx;
  font-weight: bold;
}

.detail-entry:active {
  opacity: 0.85;
}

.detail-arrow {
  font-size: 40rpx;
  font-weight: 300;
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

.status-pill.processing {
  background: #eef0f4;
  color: #374151;
}

.status-pill.success {
  background: #ecfdf3;
  color: #18a058;
}

.status-pill.cancel,
.status-pill.off {
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

.safe-bottom {
  height: 50rpx;
}

.action-row {
  margin-top: 20rpx;
}

.close-btn {
  width: 100%;
  height: 72rpx;
  line-height: 72rpx;
  border-radius: 999rpx;
  background: #fff0eb;
  color: #ff5a3c;
  font-size: 26rpx;
}

.close-btn::after {
  border: none;
}

.mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.popup {
  width: 620rpx;
  padding: 34rpx;
  border-radius: 16rpx;
  background: #ffffff;
}

.popup-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #111111;
}

.popup-desc {
  margin-top: 12rpx;
  color: #666666;
  font-size: 24rpx;
}

.form-item {
  margin-top: 24rpx;
}

.label {
  margin-bottom: 12rpx;
  color: #333333;
  font-size: 26rpx;
}

.textarea {
  width: 100%;
  min-height: 180rpx;
  padding: 20rpx;
  border-radius: 20rpx;
  background: #f6f7f9;
  box-sizing: border-box;
  font-size: 26rpx;
}

.popup-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 28rpx;
}

.popup-btn {
  flex: 1;
  height: 76rpx;
  line-height: 76rpx;
  text-align: center;
  border-radius: 999rpx;
  font-size: 28rpx;
}

.popup-btn.cancel {
  background: #f1f2f4;
  color: #666666;
}

.popup-btn.confirm {
  background: #17324d;
  color: #ffffff;
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
