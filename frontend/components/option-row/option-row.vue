<template>
  <view class="option-row">
    <view class="option-label">{{ label }}</view>
    <view class="option-wrap">
      <view
        v-for="(item, idx) in displayOptions"
        :key="idx"
        :class="['option-chip', (value === item || (item === '其他' && isOther)) ? 'active' : '']"
        @click="select(item)"
      >
        {{ item }}
      </view>
    </view>
    <textarea v-if="allowOther && isOther" class="other-note" :value="otherNote" @input="setOther" maxlength="300" placeholder="请手动填写异常情况（必填）" />
  </view>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  allowOther: { type: Boolean, default: false },
  label: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  value: { type: String, default: '' }
})
const emit = defineEmits(['select'])
const displayOptions = computed(() => props.allowOther ? [...props.options.filter(v => v !== '其他'), '其他'] : props.options)
const isOther = computed(() => props.value === '其他' || props.value.startsWith('其他：'))
const otherNote = computed(() => props.value.startsWith('其他：') ? props.value.slice(3) : '')
function select(item) { emit('select', item === '其他' && isOther.value ? props.value : item) }
function setOther(event) { emit('select', '其他：' + event.detail.value) }

</script>





<style scoped>
.other-note{width:100%;min-height:120rpx;padding:20rpx;background:#f7f9fb;border:1rpx solid #dce3eb;border-radius:10rpx;font-size:26rpx;box-sizing:border-box;}

.option-row {
  padding: 26rpx 30rpx;
  border-top: 1rpx solid #eef3f6;
  background: #ffffff;
  box-sizing: border-box;
}
.option-label {
  display: block;
  width: 100%;
  color: #222222;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 18rpx;
  line-height: 40rpx;
}
.option-wrap {
  width: 100%;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: flex-start;
  box-sizing: border-box;
}
.option-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 60rpx;
  line-height: 60rpx;
  padding: 0 24rpx;
  margin-right: 16rpx;
  margin-bottom: 16rpx;
  border-radius: 999rpx;
  background: #f4f8fb;
  color: #60656f;
  border: 2rpx solid transparent;
  font-size: 25rpx;
  box-sizing: border-box;
  white-space: nowrap;
  flex-shrink: 0;
}
.option-chip.active {
  background: #eef0f4;
  color: #374151;
  border-color: #17324d;
  font-weight: 700;
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
