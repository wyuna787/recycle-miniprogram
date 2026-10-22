<template>
  <view class="page">
    <view class="hero">
      <view class="hero-top">
        <view class="back-btn" @click="goBack">‹</view>
        <view class="hero-main">
          <view class="hello">设备详细信息</view>
          <view class="title">{{ deviceTitle }}</view>
          <view class="desc">{{ item.deviceType || item.device_type || '设备' }}</view>
        </view>
        <view class="hero-icon">{{ deviceIcon }}</view>
      </view>
    </view>

    <view class="section">
      <view class="section-title">基础信息</view>
      <view class="card">
        <view class="row" v-for="row in baseRows" :key="row.label">
          <text class="row-label">{{ row.label }}</text>
          <text class="row-value">{{ row.value }}</text>
        </view>
      </view>
    </view>

    <view v-if="detailRows.length" class="section">
      <view class="section-title">检测详情</view>
      <view class="card">
        <view class="row" v-for="row in detailRows" :key="row.label">
          <text class="row-label">{{ row.label }}</text>
          <text class="row-value">{{ row.value }}</text>
        </view>
      </view>
    </view>

    <view v-if="remarkText" class="section">
      <view class="section-title">备注</view>
      <view class="remark-card">{{ remarkText }}</view>
    </view>

    <view v-if="imageList.length" class="section">
      <view class="section-title">设备图片</view>
      <view class="photo-grid">
        <image
          v-for="(img, index) in imageList"
          :key="index"
          class="photo"
          :src="img"
          mode="aspectFill"
          @click="previewImage(index)"
        />
      </view>
    </view>

    <view v-if="orderRows.length" class="section">
      <view class="section-title">订单信息</view>
      <view class="card">
        <view class="row" v-for="row in orderRows" :key="row.label">
          <text class="row-label">{{ row.label }}</text>
          <text :class="['row-value', row.highlight ? 'highlight' : '']">{{ row.value }}</text>
        </view>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getDeviceTitle, getTradeStatusText } from '@/utils/tradeFlow.js'
import { formatMoney, calcPlatformFee, calcMerchantBaseAmount } from '@/utils/moneyMock.js'

const item = ref({})

onShow(() => {
  item.value = uni.getStorageSync('deviceDetailItem') || {}
})

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.reLaunch({ url: '/pages/home/home' })
  }
}

const deviceTitle = computed(() => getDeviceTitle(item.value))

const deviceIcon = computed(() => {
  const type = item.value.deviceType || item.value.device_type || ''
  if (type.includes('平板')) return '板'
  if (type.includes('电脑')) return '脑'
  if (type.includes('手机')) return '机'
  return '设'
})

// 兼容多种来源：顶层摊平字段 / 嵌套 device 对象（后端 serialize 始终带 device）
function val(...keys) {
  const sources = [item.value, item.value.device || {}]
  for (const src of sources) {
    for (const k of keys) {
      const v = src[k]
      if (v !== undefined && v !== null && v !== '') return v
    }
  }
  return ''
}

// 检测详情取值：顶层摊平 / item.detail / device.detail 依次回退
function detailVal(key) {
  const device = item.value.device || {}
  const sources = [
    item.value,
    item.value.detail && typeof item.value.detail === 'object' ? item.value.detail : {},
    device,
    device.detail && typeof device.detail === 'object' ? device.detail : {}
  ]
  for (const src of sources) {
    const v = src[key]
    if (v !== undefined && v !== null && v !== '') return v
  }
  return ''
}

const baseRows = computed(() => {
  const rows = [
    { label: '设备类型', value: val('deviceType', 'device_type') },
    { label: '品牌', value: val('brand') },
    { label: '型号', value: val('model') },
    { label: '成色', value: val('condition', 'screenAppearance') },
    { label: '存储容量', value: val('storage') },
    { label: '机身颜色', value: val('color') },
    { label: '购买渠道', value: val('channel') },
    { label: '保修时长', value: val('warranty') }
  ]
  return rows.map(r => ({ label: r.label, value: r.value || '-' }))
})

// 检测详情字段:仅展示当前条目中实际填写过的项
const DETAIL_FIELDS = [
  { key: 'powerOn', label: '开机情况' },
  { key: 'screenRepair', label: '屏幕维修' },
  { key: 'screenDisplay', label: '屏幕显示' },
  { key: 'screenAppearance', label: '屏幕外观' },
  { key: 'mainboard', label: '主板' },
  { key: 'batteryRepair', label: '电池维修' },
  { key: 'batteryHealth', label: '电池健康度' },
  { key: 'backCoverRepair', label: '后盖维修' },
  { key: 'partsRepair', label: '配件维修' },
  { key: 'frame', label: '边框' },
  { key: 'water', label: '进水情况' },
  { key: 'bend', label: '弯曲情况' },
  { key: 'frontCameraRepair', label: '前摄维修' },
  { key: 'rearCameraRepair', label: '后摄维修' },
  { key: 'rearPhoto', label: '后摄拍照' },
  { key: 'charge', label: '充电功能' },
  { key: 'sensor', label: '传感器' },
  { key: 'compass', label: '指南针' },
  { key: 'factory', label: '是否原厂' },
  { key: 'touch', label: '触摸' },
  { key: 'call', label: '通话' },
  { key: 'vibration', label: '震动' },
  { key: 'face', label: '面容/指纹' },
  { key: 'wireless', label: '无线充电' },
  { key: 'icloud', label: 'ID是否可注销' },
  { key: 'boot', label: '开机情况' },
  { key: 'sideButton', label: '侧键' }
]

const detailRows = computed(() => {
  return DETAIL_FIELDS
    .map(f => ({ label: f.label, value: detailVal(f.key) }))
    .filter(r => r.value !== undefined && r.value !== null && r.value !== '')
})

const remarkText = computed(() => val('remark', 'fault_desc'))

const imageList = computed(() => {
  const list = []
  const push = v => {
    if (!v) return
    if (Array.isArray(v)) {
      v.forEach(push)
    } else if (typeof v === 'string') {
      list.push(v)
    }
  }

  push(item.value.images)
  push(item.value.shippingImages)

  const photos = item.value.photos
  if (photos && typeof photos === 'object') {
    Object.keys(photos).forEach(k => push(photos[k]))
  }

  // 去重
  return list.filter((v, i) => list.indexOf(v) === i)
})

function previewImage(index) {
  uni.previewImage({
    urls: imageList.value,
    current: index
  })
}

const orderRows = computed(() => {
  const it = item.value
  const orderNo = it.order_no || it.orderNo || it.no || ''
  const price = it.price ?? it.selectedMerchantAmount ?? it.selectedAmount

  const rows = []

  if (orderNo) {
    rows.push({ label: '订单号', value: orderNo })
  }

  if (price !== undefined && price !== null && price !== '') {
    const user = uni.getStorageSync('userInfo') || {}
    const merchant = user.role === 'merchant_owner' || user.role === 'merchant_staff'
    rows.push({ label: merchant ? '成交金额' : '回收商报价', value: `¥${formatMoney(price)}`, highlight: true })
  }

  const recycler = it.selectedRecyclerCompanyName || it.recycler?.company_name
  if (recycler) {
    rows.push({ label: '成交回收商', value: recycler })
  }

  const quoteUser = it.selectedQuoteUserName
  if (quoteUser) {
    rows.push({ label: '报价员工', value: quoteUser })
  }

  const createTime = it.createTime || it.created_at
  if (createTime) {
    rows.push({ label: '创建时间', value: createTime })
  }

  if (it.tradeStatus || it.status || it.order_no || it.orderNo) {
    rows.push({ label: '当前状态', value: getTradeStatusText(it).text })
  }

  return rows
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
  align-items: flex-start;
}

.hero-main {
  flex: 1;
}

.back-btn {
  color: #fff;
  font-size: 70rpx;
  line-height: 60rpx;
  padding: 0 18rpx 0 0;
  opacity: 0.9;
  font-weight: 300;
}

.hello {
  font-size: 26rpx;
  opacity: 0.9;
}

.title {
  margin-top: 10rpx;
  font-size: 44rpx;
  font-weight: 600;
}

.desc {
  margin-top: 12rpx;
  font-size: 25rpx;
  opacity: 0.9;
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

.section {
  margin: 24rpx;
}

.section-title {
  margin-bottom: 18rpx;
  color: #222222;
  font-size: 32rpx;
  font-weight: 600;
}

.card {
  padding: 8rpx 28rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 24rpx;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #eef1f4;
}

.row:last-child {
  border-bottom: none;
}

.row-label {
  color: #888888;
  font-size: 26rpx;
}

.row-value {
  flex: 1;
  text-align: right;
  color: #222222;
  font-size: 26rpx;
  font-weight: bold;
}

.row-value.highlight {
  color: #ff5a3c;
  font-size: 30rpx;
}

.remark-card {
  padding: 26rpx;
  border-radius: 24rpx;
  background: #fff7e6;
  color: #d97706;
  font-size: 26rpx;
  line-height: 40rpx;
}

.photo-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 18rpx;
}

.photo {
  width: 210rpx;
  height: 210rpx;
  border-radius: 20rpx;
  background: #eeeeee;
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
