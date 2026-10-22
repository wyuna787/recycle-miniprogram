// /utils/moneyMock.js

const PLATFORM_FEE_RATE = 0

/**
 * 转数字，避免空值、字符串导致计算错误
 */
export function toNumber(value) {
  const num = Number(value)

  if (Number.isNaN(num)) {
    return 0
  }

  return num
}

/**
 * 金额保留两位小数
 */
export function formatMoney(value) {
  return toNumber(value).toFixed(2)
}

/**
 * 工作台展示金额：去掉小数点后数字
 * 注意：不是四舍五入，是直接向下取整
 */
export function formatDisplayMoney(value) {
  return Math.floor(toNumber(value))
}

/**
 * 计算平台服务费
 * 平台固定抽旧机设备成交价格 2%
 */
export function calcPlatformFee(recyclerQuoteAmount) {
  const amount = toNumber(recyclerQuoteAmount)

  return roundMoney(amount * PLATFORM_FEE_RATE)
}

/**
 * 计算平台扣费后的商家基础金额
 * 商家端可以看到这个结果，但不显示平台服务费明细
 */
export function calcMerchantBaseAmount(recyclerQuoteAmount) {
  const amount = toNumber(recyclerQuoteAmount)
  const platformFee = calcPlatformFee(amount)

  return roundMoney(amount - platformFee)
}

/**
 * 计算老板抽成金额
 */
export function calcOwnerCommission(merchantBaseAmount, ownerRate) {
  const base = toNumber(merchantBaseAmount)
  const rate = toNumber(ownerRate)

  return roundMoney(base * rate)
}

/**
 * 计算员工抽成金额
 */
export function calcStaffCommission(merchantBaseAmount, staffRate) {
  const base = toNumber(merchantBaseAmount)
  const rate = toNumber(staffRate)

  return roundMoney(base * rate)
}

/**
 * 回收商报价时生成报价金额快照
 *
 * recyclerQuoteAmount：回收商完整报价金额
 * ownerRate：商家老板抽成比例
 * staffRate：商家员工抽成比例
 *
 * 说明：
 * 1. 平台管理员端可看完整拆分
 * 2. 商家端不显示 platformFeeAmount 明细
 * 3. 商家端只显示 merchantTip：已扣除平台 2% 服务费
 */
export function buildQuoteAmountSnapshot({
  recyclerQuoteAmount,
  ownerRate = 0,
  staffRate = 0
}) {
  const fullAmount = roundMoney(recyclerQuoteAmount)
  const platformFeeAmount = calcPlatformFee(fullAmount)
  const merchantBaseAmount = calcMerchantBaseAmount(fullAmount)

  const ownerCommission = calcOwnerCommission(merchantBaseAmount, ownerRate)
  const staffCommission = calcStaffCommission(merchantBaseAmount, staffRate)

  const merchantRealAmount = roundMoney(
    merchantBaseAmount - ownerCommission - staffCommission
  )

  const merchantDisplayAmount = formatDisplayMoney(merchantRealAmount)

  return {
    // 回收商完整报价金额
    recyclerQuoteAmount: fullAmount,

    // 平台服务费，仅平台管理员端展示
    platformFeeRate: PLATFORM_FEE_RATE,
    platformFeeAmount,

    // 商家端基础可见金额，已扣除平台服务费
    merchantBaseAmount,

    // 商家端提示，不展示具体平台服务费金额
    merchantTip: '已扣除平台 2% 服务费',

    // 商家老板抽成
    merchantOwnerRate: toNumber(ownerRate),
    merchantOwnerCommission: ownerCommission,

    // 商家员工抽成
    merchantStaffRate: toNumber(staffRate),
    merchantStaffCommission: staffCommission,

    // 内部真实金额，数据分析页可看
    merchantRealAmount,

    // 工作台展示给卖机用户看的金额，去掉小数
    merchantDisplayAmount
  }
}

/**
 * 商家端报价卡片展示数据
 *
 * 商家端不返回 platformFeeAmount，避免显示平台 2% 明细。
 */
export function buildMerchantQuoteView(quote, options = {}) {
  const ownerRate = toNumber(options.ownerRate)
  const staffRate = toNumber(options.staffRate)

  const snapshot = buildQuoteAmountSnapshot({
    recyclerQuoteAmount: quote.recyclerQuoteAmount || quote.amount || 0,
    ownerRate,
    staffRate
  })

  return {
    quoteId: quote.id,
    recyclerCompanyId: quote.recyclerCompanyId,
    recyclerCompanyName: quote.recyclerCompanyName,
    quoteUserId: quote.quoteUserId,
    quoteUserName: quote.quoteUserName,
    quoteTime: quote.quoteTime,

    // 商家端主展示金额
    merchantBaseAmount: snapshot.merchantBaseAmount,
    merchantRealAmount: snapshot.merchantRealAmount,
    merchantDisplayAmount: snapshot.merchantDisplayAmount,

    // 商家端只显示这句提示
    merchantTip: snapshot.merchantTip,

    // 商家老板/员工内部可看抽成
    merchantOwnerRate: snapshot.merchantOwnerRate,
    merchantOwnerCommission: snapshot.merchantOwnerCommission,
    merchantStaffRate: snapshot.merchantStaffRate,
    merchantStaffCommission: snapshot.merchantStaffCommission
  }
}

/**
 * 平台管理员端报价展示数据
 *
 * 平台管理员可看完整金额拆分。
 */
export function buildPlatformQuoteView(quote, options = {}) {
  const ownerRate = toNumber(options.ownerRate)
  const staffRate = toNumber(options.staffRate)

  const snapshot = buildQuoteAmountSnapshot({
    recyclerQuoteAmount: quote.recyclerQuoteAmount || quote.amount || 0,
    ownerRate,
    staffRate
  })

  return {
    quoteId: quote.id,
    recyclerCompanyId: quote.recyclerCompanyId,
    recyclerCompanyName: quote.recyclerCompanyName,
    quoteUserId: quote.quoteUserId,
    quoteUserName: quote.quoteUserName,
    quoteTime: quote.quoteTime,

    recyclerQuoteAmount: snapshot.recyclerQuoteAmount,

    platformFeeRate: snapshot.platformFeeRate,
    platformFeeAmount: snapshot.platformFeeAmount,

    merchantBaseAmount: snapshot.merchantBaseAmount,

    merchantOwnerRate: snapshot.merchantOwnerRate,
    merchantOwnerCommission: snapshot.merchantOwnerCommission,

    merchantStaffRate: snapshot.merchantStaffRate,
    merchantStaffCommission: snapshot.merchantStaffCommission,

    merchantRealAmount: snapshot.merchantRealAmount,
    merchantDisplayAmount: snapshot.merchantDisplayAmount
  }
}

/**
 * 回收商端报价展示数据
 *
 * 回收商端主要看自己的完整报价和商家基础金额。
 * 默认不展示平台服务费明细，减少对账解释成本。
 */
export function buildRecyclerQuoteView(quote) {
  const snapshot = buildQuoteAmountSnapshot({
    recyclerQuoteAmount: quote.recyclerQuoteAmount || quote.amount || 0
  })

  return {
    quoteId: quote.id,
    recyclerCompanyId: quote.recyclerCompanyId,
    recyclerCompanyName: quote.recyclerCompanyName,
    quoteUserId: quote.quoteUserId,
    quoteUserName: quote.quoteUserName,
    quoteTime: quote.quoteTime,

    recyclerQuoteAmount: snapshot.recyclerQuoteAmount,
    merchantBaseAmount: snapshot.merchantBaseAmount,

    merchantTip: snapshot.merchantTip
  }
}

/**
 * 商家确认成交时生成成交金额快照
 *
 * 这个快照必须保存到订单里，避免以后抽成比例变化影响历史订单。
 */
export function buildDealAmountSnapshot({
  quote,
  ownerRate = 0,
  staffRate = 0
}) {
  const snapshot = buildQuoteAmountSnapshot({
    recyclerQuoteAmount: quote.recyclerQuoteAmount || quote.amount || 0,
    ownerRate,
    staffRate
  })

  return {
    selectedQuoteId: quote.id,

    selectedRecyclerCompanyId: quote.recyclerCompanyId,
    selectedRecyclerCompanyName: quote.recyclerCompanyName,
    selectedQuoteUserId: quote.quoteUserId,
    selectedQuoteUserName: quote.quoteUserName,

    selectedRecyclerQuoteAmount: snapshot.recyclerQuoteAmount,

    selectedPlatformFeeRate: snapshot.platformFeeRate,
    selectedPlatformFeeAmount: snapshot.platformFeeAmount,

    selectedMerchantBaseAmount: snapshot.merchantBaseAmount,

    selectedMerchantOwnerRate: snapshot.merchantOwnerRate,
    selectedMerchantOwnerCommission: snapshot.merchantOwnerCommission,

    selectedMerchantStaffRate: snapshot.merchantStaffRate,
    selectedMerchantStaffCommission: snapshot.merchantStaffCommission,

    selectedMerchantRealAmount: snapshot.merchantRealAmount,
    selectedMerchantDisplayAmount: snapshot.merchantDisplayAmount,

    merchantTip: snapshot.merchantTip
  }
}

/**
 * 获取商家端订单金额展示
 *
 * 商家端不展示平台服务费金额，只展示提示。
 */
export function getMerchantOrderAmountView(order) {
  return {
    merchantBaseAmount: order.selectedMerchantBaseAmount || 0,
    merchantRealAmount: order.selectedMerchantRealAmount || 0,
    merchantDisplayAmount: order.selectedMerchantDisplayAmount || 0,
    merchantTip: order.merchantTip || '已扣除平台 2% 服务费',

    merchantOwnerCommission: order.selectedMerchantOwnerCommission || 0,
    merchantStaffCommission: order.selectedMerchantStaffCommission || 0
  }
}

/**
 * 获取平台端订单金额展示
 *
 * 平台端可看完整金额拆分。
 */
export function getPlatformOrderAmountView(order) {
  return {
    recyclerQuoteAmount: order.selectedRecyclerQuoteAmount || 0,

    platformFeeRate: order.selectedPlatformFeeRate || PLATFORM_FEE_RATE,
    platformFeeAmount: order.selectedPlatformFeeAmount || 0,

    merchantBaseAmount: order.selectedMerchantBaseAmount || 0,

    merchantOwnerRate: order.selectedMerchantOwnerRate || 0,
    merchantOwnerCommission: order.selectedMerchantOwnerCommission || 0,

    merchantStaffRate: order.selectedMerchantStaffRate || 0,
    merchantStaffCommission: order.selectedMerchantStaffCommission || 0,

    merchantRealAmount: order.selectedMerchantRealAmount || 0,
    merchantDisplayAmount: order.selectedMerchantDisplayAmount || 0
  }
}

/**
 * 四舍五入到 2 位小数
 */
function roundMoney(value) {
  const num = toNumber(value)

  return Math.round(num * 100) / 100
}