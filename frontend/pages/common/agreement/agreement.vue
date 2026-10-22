<template>
  <view class="doc-page">
    <view class="doc-title">用户服务协议</view>
    <view class="doc-update">更新日期：2026年6月23日</view>

    <view class="doc-section">
      <view class="h">一、协议的范围</view>
      <view class="p">欢迎使用「中晨回收」小程序（以下简称“本小程序”）。本协议是您与本小程序运营方（以下简称“我们”）之间就使用本小程序服务所订立的协议。您注册、登录或使用本小程序，即表示您已阅读并同意接受本协议的全部条款。</view>
    </view>

    <view class="doc-section">
      <view class="h">二、账号注册与使用</view>
      <view class="p">1. 您在使用本小程序前需注册账号，并需提供真实、准确、完整的手机号、姓名/昵称等信息。</view>
      <view class="p">2. 账号注册后需经平台管理员审核通过方可登录使用。</view>
      <view class="p">3. 您应妥善保管账号及密码，因您保管不善造成的损失由您自行承担。</view>
    </view>

    <view class="doc-section">
      <view class="h">三、服务内容</view>
      <view class="p">本小程序为二手电子设备回收交易提供信息撮合服务，包括设备发布、询价、报价、下单、发货、验机、结算等功能。</view>
    </view>

    <view class="doc-section">
      <view class="h">四、用户行为规范</view>
      <view class="p">您承诺不利用本小程序从事违法违规活动，不发布虚假信息，不损害他人合法权益。</view>
    </view>

    <view class="doc-section">
      <view class="h">五、个人信息保护</view>
      <view class="p">我们将依照《隐私政策》收集、使用和保护您的个人信息。请您在使用前一并阅读《隐私政策》。</view>
    </view>

    <view class="doc-section">
      <view class="h">六、协议的变更</view>
      <view class="p">我们有权根据需要修改本协议，修改后的协议将在本小程序公布。如您继续使用，即视为接受修改后的协议。</view>
    </view>

    <view class="doc-section">
      <view class="h">七、联系我们</view>
      <view class="p">如对本协议有任何疑问，可通过小程序内的联系方式与我们联系。</view>
    </view>

    <view class="doc-foot">中晨回收</view>
  </view>
</template>

<script setup>
</script>





<style scoped>

.doc-page {
  padding: 40rpx 36rpx 80rpx;
  background: #ffffff;
  min-height: 100vh;
}
.doc-title {
  font-size: 40rpx;
  font-weight: 700;
  color: #1f2937;
  text-align: center;
}
.doc-update {
  font-size: 24rpx;
  color: #9ca3af;
  text-align: center;
  margin: 12rpx 0 36rpx;
}
.doc-section {
  margin-bottom: 32rpx;
}
.h {
  font-size: 30rpx;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12rpx;
}
.p {
  font-size: 27rpx;
  color: #17324d;
  line-height: 44rpx;
  margin-bottom: 8rpx;
}
.doc-foot {
  margin-top: 48rpx;
  text-align: center;
  font-size: 24rpx;
  color: #9ca3af;
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
