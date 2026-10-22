<template>
  <view class="report">
    <view class="title">验机照片</view>
    <view class="photos"><image v-for="(url,i) in photos" :key="url" :src="url" mode="aspectFill" @click="preview(i)" /></view>
    <view v-if="!photos.length" class="muted">暂无照片</view>
    <view class="title">验机报告</view>
    <view class="row" v-for="row in baseRows" :key="row.label"><text>{{ row.label }}</text><text>{{ row.value || '-' }}</text></view>
    <view class="title">备注</view><view class="remark">{{ item.remark || item.fault_desc || device.fault_desc || '无' }}</view>
    <view class="title bad">异常项（{{ badRows.length }}项）</view>
    <view class="row bad" v-for="row in badRows" :key="row.label"><text>{{ row.label }}</text><text>{{ row.value }}</text></view>
    <view v-if="!badRows.length" class="muted">未标注异常项</view>
    <view class="title">正常项（{{ goodRows.length }}项）</view>
    <view class="row" v-for="row in goodRows" :key="row.label"><text>{{ row.label }}</text><text>{{ row.value }}</text></view>
    <view class="title">订单详情</view>
    <view class="row" v-for="row in orderRows" :key="row.label"><text>{{ row.label }}</text><text selectable @click="copyNumber(row)">{{ row.value || '-' }}<text v-if="copyable(row)"> · 复制</text></text></view>
  </view>
</template>
<script setup>
import { computed } from 'vue'
import { isAbnormalDeviceValue } from '@/utils/device-condition.js'
const props = defineProps({ item: { type: Object, default: () => ({}) } })
const device = computed(() => props.item.device || props.item)
const value = key => props.item[key] ?? props.item.detail?.[key] ?? device.value[key] ?? device.value.detail?.[key] ?? ''
const fields = { powerOn:'开机情况',idLock:'ID锁',screenLock:'锁屏密码',screenRepair:'屏幕维修',screenDisplay:'屏幕显示',screenAppearance:'屏幕外观',mainboard:'主板',batteryRepair:'电池维修',batteryHealth:'电池健康度',backCoverRepair:'后盖维修',partsRepair:'配件维修',frame:'边框',water:'进水情况',bend:'弯曲情况',frontCameraRepair:'前摄维修',rearCameraRepair:'后摄维修',rearPhoto:'后摄拍照',charge:'充电',sensor:'传感器',compass:'指南针',factory:'是否原厂',touch:'触摸',call:'通话',vibration:'震动',face:'面容/指纹',wireless:'无线充电',icloud:'ID可注销',boot:'开机细节',sideButton:'侧键' }
const rows = computed(() => Object.keys(fields).map(key => ({key,label:fields[key],value:value(key)})).filter(row=>row.value!==''))
const badRows = computed(()=>rows.value.filter(row=>isAbnormalDeviceValue(row.key,row.value)))
const goodRows = computed(()=>rows.value.filter(row=>!isAbnormalDeviceValue(row.key,row.value)))
const baseRows = computed(()=>[
 {label:'设备类型',value:value('device_type') || value('deviceType')}, {label:'型号',value:[value('brand'),value('model')].join(' ')},
 {label:'成色',value:value('condition')}, {label:'内存',value:value('storage')}, {label:'机身颜色',value:value('color')},
 {label:'购买渠道',value:value('channel')},{label:'保修时长',value:value('warranty')}, {label:'IMEI',value:value('imei')}
])
const orderRows = computed(()=>[
 {label:'订单号',value:props.item.order_no || props.item.orderNo}, {label:'询价单号',value:props.item.no || (props.item.inquiry_id ? `XJ${props.item.inquiry_id}` : `XJ${props.item.id}`)},
 {label:'商家',value:props.item.merchantCompanyName || props.item.merchant?.company_name}, {label:'发布时间',value:props.item.created_at || props.item.createTime},
 {label:'报价截止',value:props.item.quote_deadline}, {label:'快递公司',value:props.item.express_company}, {label:'快递单号',value:props.item.tracking_no}
])
const photos = computed(()=>{
 const list=[...(props.item.images || []),...(device.value.images || [])]
 const grouped=props.item.photos || device.value.detail?.photos || {}
 Object.values(grouped).forEach(v=>{if(Array.isArray(v))list.push(...v);else if(typeof v==='string')list.push(v)})
 return [...new Set(list.filter(Boolean))]
})
function copyable(row){return ['订单号','询价单号','快递单号'].includes(row.label) && !!row.value && row.value!=='-'}
function copyNumber(row){if(copyable(row))uni.setClipboardData({data:String(row.value)})}
function preview(i) { uni.previewImage({urls:photos.value,current:photos.value[i]}) }
</script>




<style scoped>

.report{background:#fff;border-radius:24rpx;padding:28rpx;margin-top:20rpx}.title{font-size:30rpx;font-weight:bold;margin:24rpx 0 16rpx}.row{display:flex;justify-content:space-between;gap:20rpx;padding:14rpx 0;border-bottom:1rpx solid #eef1f4;font-size:26rpx}.row text:last-child{text-align:right;overflow-wrap:anywhere}.bad{color:#e54848}.muted{color:#888}.photos{display:flex;flex-wrap:wrap;gap:12rpx}.photos image{width:140rpx;height:140rpx;border-radius:14rpx}.remark{white-space:pre-wrap;font-size:26rpx;color:#555}



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
