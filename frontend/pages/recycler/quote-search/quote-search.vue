<template>
  <view class="page">
    <custom-navbar title="单号查询报价" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ currentUser.username || '回收商' }}</view>
          <view class="title">单号查询</view>
          <view class="desc">
            凭订单 / 询价编号查询本公司报价记录，查看同事报价与成交状态。
          </view>
        </view>

        <view class="hero-icon">查</view>
      </view>

      <view class="search-box">
        <input
          class="search-input"
          v-model="keyword"
          placeholder="请输入订单号 / 询价编号"
          confirm-type="search"
          @confirm="doSearch"
        />
        <view class="search-btn" @click="doSearch">查询</view>
      </view>
    </view>

    <view class="rule-card">
      <view class="rule-line">· 仅能凭单号查询，不能浏览全部订单。</view>
      <view class="rule-line">· 只能查看，不能修改他人报价。</view>
      <view class="rule-line">· 不展示完整资金池财务数据。</view>
    </view>

    <view v-if="searched && !result" class="empty">
      未查询到该单号对应的报价记录
    </view>

    <view v-if="result" class="result-card">
      <view class="card-head">
        <view>
          <view class="device-name">{{ getDeviceTitle(result) }}</view>
          <view class="order-no">单号：{{ result.orderNo || result.no || result.id }}</view>
        </view>

        <view :class="['deal-pill', dealClass]">{{ dealText }}</view>
      </view>

      <view class="info-box">
        <view class="info-row">
          <text>商家公司</text>
          <text>{{ result.merchantCompanyName || result.company_name || '-' }}</text>
        </view>
        <view class="info-row">
          <text>设备类型</text>
          <text>{{ result.deviceType || result.device_type || '-' }}</text>
        </view>
      </view>

      <view class="quote-title">本公司报价记录（{{ companyQuotes.length }} 条）</view>

      <view v-if="companyQuotes.length === 0" class="empty-inline">
        本公司暂无报价记录
      </view>

      <view
        v-for="quote in companyQuotes"
        :key="quote.id"
        :class="['quote-row', isSelected(quote) ? 'selected' : '']"
      >
        <view class="quote-main">
          <view class="quote-money">¥{{ formatMoney(quote.recyclerQuoteAmount || quote.amount) }}</view>
          <view class="quote-meta">
            报价员工：{{ quote.quoteUserName || '-' }} · {{ quote.quoteTime || '-' }}
          </view>
        </view>

        <view :class="['quote-tag', isSelected(quote) ? 'win' : '']">
          {{ isSelected(quote) ? '已成交' : '已报价' }}
        </view>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { formatMoney } from '@/utils/moneyMock.js'
import { getDeviceTitle } from '@/utils/tradeFlow.js'
import { lookupCompanyQuotes } from '@/api/trade.js'

const currentUser = ref({})
const searching = ref(false)
const keyword = ref('')
const searched = ref(false)
const result = ref(null)

onLoad(() => {
  currentUser.value = uni.getStorageSync('userInfo') || uni.getStorageSync('currentUser') || {}

  if (!currentUser.value.role) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }

})

// 只展示本公司的报价记录(不泄露其他回收商)
const companyQuotes = computed(() => {
  if (!result.value) return []

  const quotes = Array.isArray(result.value.quotes) ? result.value.quotes : []

  return quotes.filter(item => {
    return Number(item.recyclerCompanyId) === Number(currentUser.value.company_id)
  })
})

const isAccepted = computed(() => {
  if (!result.value) return false
  return result.value.status === '商家已接单' || result.value.quoteStatus === 'accepted'
})

const acceptedByMyCompany = computed(() => {
  return isAccepted.value &&
    Number(result.value.selectedRecyclerCompanyId) === Number(currentUser.value.company_id)
})

const dealText = computed(() => {
  if (!result.value) return ''
  if (acceptedByMyCompany.value) return '商家已确认成交'
  if (isAccepted.value) return '其他回收商成交'
  if (result.value.status === 'expired') return '报价已结束'
  return '等待商家确认'
})

const dealClass = computed(() => {
  if (acceptedByMyCompany.value) return 'success'
  if (isAccepted.value) return 'gray'
  return 'waiting'
})

function isSelected(quote) {
  return acceptedByMyCompany.value &&
    Number(result.value.selectedQuoteId) === Number(quote.id)
}

async function doSearch() {
  if (searching.value) return
  const key = keyword.value.trim()
  result.value = null
  searched.value = false
  if (!key) {
    uni.showToast({ title: '请输入单号', icon: 'none' })
    return
  }
  searching.value = true
  try {
    const response = await lookupCompanyQuotes(key)
    result.value = response.item || null
    searched.value = true
  } catch (error) {
    // 请求组件显示错误，不把网络失败误报成无记录。
  } finally {
    searching.value = false
  }
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

.search-box {
  margin-top: 30rpx;
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.search-input {
  flex: 1;
  height: 84rpx;
  padding: 0 24rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.92);
  color: #222222;
  font-size: 28rpx;
  box-sizing: border-box;
}

.search-btn {
  width: 140rpx;
  height: 84rpx;
  line-height: 84rpx;
  text-align: center;
  border-radius: 22rpx;
  background: #ffffff;
  color: #374151;
  font-size: 28rpx;
  font-weight: bold;
}

.rule-card {
  margin: 0 24rpx 24rpx;
  padding: 24rpx;
  border-radius: 16rpx;
  background: #fff7e6;
}

.rule-line {
  color: #9a6200;
  font-size: 24rpx;
  line-height: 38rpx;
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

.result-card {
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

.device-name {
  color: #111111;
  font-size: 32rpx;
  font-weight: 600;
}

.order-no {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.deal-pill {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
  font-weight: bold;
}

.deal-pill.success {
  background: #ecfdf3;
  color: #18a058;
}

.deal-pill.waiting {
  background: #fff7e6;
  color: #d97706;
}

.deal-pill.gray {
  background: #eef2f7;
  color: #667085;
}

.info-box {
  margin-top: 22rpx;
  padding: 20rpx;
  border-radius: 20rpx;
  background: #f6f7f9;
}

.info-row {
  display: flex;
  justify-content: space-between;
  color: #666666;
  font-size: 24rpx;
  line-height: 42rpx;
}

.quote-title {
  margin-top: 26rpx;
  margin-bottom: 6rpx;
  color: #222222;
  font-size: 27rpx;
  font-weight: 600;
}

.quote-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #eef1f4;
}

.quote-row:last-child {
  border-bottom: none;
}

.quote-row.selected {
  background: #f6fffb;
}

.quote-money {
  color: #ff5a3c;
  font-size: 32rpx;
  font-weight: 600;
}

.quote-meta {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 24rpx;
}

.quote-tag {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: #eef0f4;
  color: #374151;
  font-size: 24rpx;
  font-weight: bold;
}

.quote-tag.win {
  background: #ecfdf3;
  color: #18a058;
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
