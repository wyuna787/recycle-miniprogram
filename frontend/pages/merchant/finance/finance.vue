<template>
 <view class="page"><custom-navbar title="资金账户" />
  <view class="hero"><view class="hello">商家资金</view><view class="title">成交与收益</view><view class="desc">金额按订单确认时的收益比例计算</view></view>
  <view v-if="error" class="empty" @click="load">加载失败，点击重试</view>
  <view v-else class="section"><view class="section-title">订单资金概览</view><view class="info-row"><text>已结算成交金额</text><text>¥{{ money(settled) }}</text></view><view class="info-row"><text>我的已结算收益</text><text>¥{{ money(income) }}</text></view><view class="info-row"><text>待结算成交金额</text><text>¥{{ money(pending) }}</text></view><view class="hint">{{ loading ? '加载中…' : '以当前账号可查看的订单为准' }}</view></view>
  <view class="section"><button class="primary-btn" @click="go('/pages/merchant/commission/commission')">设置我的收益比例</button><button class="secondary-btn" @click="go('/pages/merchant/order/order')">查询订单明细</button></view>
 </view>
</template>
<script setup>
import {ref,computed} from 'vue'
import {onShow} from '@dcloudio/uni-app'
import {getMyOrders} from '@/api/trade.js'
const rows=ref([]),loading=ref(false),error=ref(false)
const total=(list,field)=>list.reduce((sum,row)=>sum+Number(row[field] || 0),0)
const settledRows=computed(()=>rows.value.filter(row=>row.fund_status==='deducted' && !['cancelled','closed'].includes(row.status)))
const settled=computed(()=>total(settledRows.value,'price'))
const income=computed(()=>total(settledRows.value,'myCommission'))
const pending=computed(()=>total(rows.value.filter(row=>row.fund_status!=='deducted' && !['cancelled','closed'].includes(row.status)),'price'))
const money=value=>Number(value || 0).toFixed(2)
const go=url=>uni.navigateTo({url})
async function load(){loading.value=true;error.value=false;try{rows.value=(await getMyOrders()).list || []}catch(e){error.value=true}finally{loading.value=false}}
onShow(load)
</script>
<style scoped>
.section{margin:24rpx;padding:28rpx}.info-row{display:flex;justify-content:space-between;padding:24rpx 0;border-bottom:1rpx solid #e2e8f0;font-size:28rpx}.secondary-btn{margin-top:20rpx;background:#eef3f7;color:#17324d;border-radius:10rpx}
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