<template>
  <view class="page">
    <custom-navbar title="我的钱包" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ roleLabel }}</view>
          <view class="title">我的钱包</view>
          <view class="desc">
            老板与员工分别设置自己的比例，互不联动。已成交订单按确认时的比例结算。
          </view>
        </view>

        <view class="hero-icon">成</view>
      </view>

      <view class="rate-card">
        <view class="rate-label">当前收益比例</view>
        <view class="rate-value">{{ (savedRate * 100).toFixed(2) }}%</view>
      </view>
    </view>

    <view class="section">
      <view class="section-title">{{ isOwner ? '老板收益比例' : '员工收益比例' }}</view>

      <view class="form-item">
        <view class="label">收益比例（%）</view>
        <input
          class="input"
          type="digit"
          v-model="rateInput"
          placeholder="例如：10 表示 10%"
        />
        <view class="hint">范围 0 ~ 100，可填小数，如 12.5</view>
      </view>

      <view v-if="rateInput !== ''" class="preview-card">
        <view class="preview-title">按成交金额 ¥1000 试算</view>
        <view class="preview-row">
          <text>成交金额</text>
          <text>¥{{ formatMoney(baseAfterPlatform) }}</text>
        </view>
        <view class="preview-row">
          <text>我的收益</text>
          <text class="strong">¥{{ formatMoney(previewAmount) }}</text>
        </view>
      </view>

      <button class="save-btn" @click="saveRate">保存比例</button>
    </view>

    <view v-if="isOwner" class="section">
      <view class="section-title">员工收益一览</view>

      <view v-if="staffRows.length === 0" class="empty-inline">
        暂无员工收益记录
      </view>

      <view
        v-for="staff in staffRows"
        :key="staff.userId"
        class="staff-row"
      >
        <text class="staff-name">{{ staff.userName }}</text>
        <text class="staff-rate">{{ (staff.rate * 100).toFixed(2) }}%</text>
      </view>

      <view class="owner-note">老板可查看员工收益，但不能代员工修改。</view>
    </view>


    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { formatMoney, calcMerchantBaseAmount, toNumber } from '@/utils/moneyMock.js'
import { getCommissionRate, getCommissionRates, setCommissionRate } from '@/api/fund.js'


const currentUser = ref({})
const rateInput = ref('')
const savedRate = ref(0)
const staffRows = ref([])

onShow(() => {
  currentUser.value = uni.getStorageSync('userInfo') || uni.getStorageSync('currentUser') || {}

  if (!isMerchantRole(currentUser.value.role)) {
    uni.showToast({ title: '仅商家账号可设置', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 600)
    return
  }

  loadData()
})

const isOwner = computed(() => currentUser.value.role === 'merchant_owner')

const roleLabel = computed(() => {
  return currentUser.value.role === 'merchant_owner' ? '商家老板' : '商家员工'
})

// 按成交金额 ¥1000 试算分成
const baseAfterPlatform = computed(() => 1000)

const previewAmount = computed(() => {
  const rate = normalizeRate(rateInput.value)
  return Math.round(baseAfterPlatform.value * rate * 100) / 100
})

function isMerchantRole(role) {
  return role === 'merchant_owner' || role === 'merchant_staff'
}

function normalizeRate(value) {
  const num = toNumber(value)
  return num / 100
}

async function loadData() {
  try {
    const mineRes = await getCommissionRate(currentUser.value.id)
    const mineRate = Number(mineRes.rate || 0)
    savedRate.value = mineRate
    rateInput.value = mineRate ? String((mineRate * 100).toFixed(2)) : ''

    if (isOwner.value) {
      const res = await getCommissionRates(currentUser.value.company_id)
      staffRows.value = (res.list || [])
        .filter(item => item.role === 'merchant_staff')
        .map(item => ({
          userId: item.user_id,
          userName: item.username || `员工${item.user_id}`,
          rate: Number(item.rate || 0)
        }))
    }
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

}

async function saveRate() {
  const num = Number(rateInput.value)

  if (!rateInput.value.trim() || !Number.isFinite(num) || num < 0 || num > 100) {
    uni.showToast({ title: '请输入 0~100 的比例', icon: 'none' })
    return
  }

  const rate = normalizeRate(rateInput.value)

  try {
    await setCommissionRate(currentUser.value.id, rate)
    savedRate.value = rate
    uni.showToast({ title: '已保存', icon: 'success' })
    await loadData()
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
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

.rate-card {
  margin-top: 30rpx;
  padding: 26rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.2);
}

.rate-label {
  font-size: 24rpx;
  opacity: 0.9;
}

.rate-value {
  margin-top: 8rpx;
  font-size: 52rpx;
  font-weight: 600;
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

.form-item {
  margin-bottom: 8rpx;
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
  font-size: 32rpx;
  box-sizing: border-box;
}

.hint {
  margin-top: 12rpx;
  color: #64748b;
  font-size: 24rpx;
}

.preview-card {
  margin-top: 22rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f6f7f9;
}

.preview-title {
  color: #64748b;
  font-size: 24rpx;
  margin-bottom: 12rpx;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  color: #555555;
  font-size: 25rpx;
  line-height: 42rpx;
}

.preview-row .strong {
  color: #ff5a3c;
  font-weight: 600;
}

.save-btn {
  margin-top: 24rpx;
  height: 82rpx;
  line-height: 82rpx;
  border-radius: 999rpx;
  background: #17324d;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: bold;
}

.save-btn::after {
  border: none;
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

.staff-rate {
  color: #374151;
  font-size: 27rpx;
  font-weight: 600;
}

.empty-inline {
  padding: 30rpx;
  text-align: center;
  color: #64748b;
  font-size: 25rpx;
}

.owner-note {
  margin-top: 14rpx;
  color: #64748b;
  font-size: 24rpx;
}

.rule-card {
  margin: 24rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  background: #fff7e6;
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
