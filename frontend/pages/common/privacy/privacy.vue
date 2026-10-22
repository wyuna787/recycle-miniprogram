<template>
  <view class="doc-page">
    <view class="doc-title">隐私政策</view>
    <view class="doc-update">更新日期：2026年6月23日</view>

    <view class="doc-section">
      <view class="p">「中晨回收」小程序（以下简称“本小程序”）非常重视您的个人信息和隐私保护。本政策旨在向您说明我们如何收集、使用、存储和保护您的个人信息，以及您享有的权利。请您在使用前仔细阅读。</view>
    </view>

    <view class="doc-section">
      <view class="h">一、我们收集的信息</view>
      <view class="p">1. 账号信息：注册、登录时您提供的手机号、姓名/昵称、密码、申请身份及所属公司信息。</view>
      <view class="p">2. 业务信息：您在发布设备、询价、下单等过程中填写的设备信息、订单信息及上传的图片。</view>
      <view class="p">3. 我们仅收集为提供服务所必需的信息。</view>
    </view>

    <view class="doc-section">
      <view class="h">二、信息的使用目的</view>
      <view class="p">1. 用于账号注册、登录、身份审核与管理；</view>
      <view class="p">2. 用于完成二手设备回收交易的撮合、订单处理与结算；</view>
      <view class="p">3. 用于保障账号与交易安全、改进服务质量。</view>
    </view>

    <view class="doc-section">
      <view class="h">三、信息的存储与保护</view>
      <view class="p">我们采取合理的技术与管理措施保护您的个人信息，防止信息丢失、泄露或被非法访问。您的信息存储于我们的服务器，存储期限为提供服务所必需的期间及法律要求的期限。</view>
    </view>

    <view class="doc-section">
      <view class="h">四、信息的对外提供</view>
      <view class="p">未经您同意，我们不会向第三方共享、转让您的个人信息，但为完成交易撮合而向交易相对方展示的必要信息（如报价、订单状态）除外，以及法律法规要求的情形除外。</view>
    </view>

    <view class="doc-section">
      <view class="h">五、您的权利</view>
      <view class="p">您有权查询、更正您的个人信息，并可申请注销账号。注销后我们将删除或匿名化您的个人信息，法律另有规定的除外。</view>
    </view>

    <view class="doc-section">
      <view class="h">六、未成年人保护</view>
      <view class="p">本小程序主要面向企业及成年用户。若您为未成年人，请在监护人指导下使用。</view>
    </view>

    <view class="doc-section">
      <view class="h">七、联系我们</view>
      <view class="p">如对本隐私政策有任何疑问或投诉，可通过小程序内的联系方式与我们联系。</view>
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
