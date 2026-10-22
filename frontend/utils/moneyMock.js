const PLATFORM_FEE_RATE = 0.02

export function toNumber(value) {
  const num = Number(value)

  if (Number.isNaN(num)) {
    return 0
  }

  return num
}

export function formatMoney(value) {
  return toNumber(value).toFixed(2)
}

export function formatDisplayMoney(value) {
  return Math.floor(toNumber(value))
}

export { PLATFORM_FEE_RATE }

export function calcPlatformFee(recyclerQuoteAmount) {
  const amount = toNumber(recyclerQuoteAmount)

  return roundMoney(amount * PLATFORM_FEE_RATE)
}

// 真实成交金额 = 回收商报价 − 平台2% = 报价 × 0.98
export function calcMerchantBaseAmount(recyclerQuoteAmount) {
  const amount = toNumber(recyclerQuoteAmount)

  return roundMoney(amount - amount * PLATFORM_FEE_RATE)
}

export function calcOwnerCommission(merchantBaseAmount, ownerRate) {
  const base = toNumber(merchantBaseAmount)
  const rate = toNumber(ownerRate)

  return roundMoney(base * rate)
}

export function calcStaffCommission(merchantBaseAmount, staffRate) {
  const base = toNumber(merchantBaseAmount)
  const rate = toNumber(staffRate)

  return roundMoney(base * rate)
}

export function buildQuoteAmountSnapshot({
  recyclerQuoteAmount,
  ownerRate = 0,
  staffRate = 0
}) {
  const fullAmount = roundMoney(recyclerQuoteAmount)
  const platformFeeAmount = calcPlatformFee(fullAmount)
  // 真实成交金额 = 报价 − 平台2%
  const merchantRealAmount = roundMoney(fullAmount - platformFeeAmount)
  const merchantBaseAmount = merchantRealAmount

  // 抽成按「报价」算（不减平台费）
  const ownerCommission = calcOwnerCommission(fullAmount, ownerRate)
  const staffCommission = calcStaffCommission(fullAmount, staffRate)

  const merchantDisplayAmount = formatDisplayMoney(merchantRealAmount)

  return {
    recyclerQuoteAmount: fullAmount,

    platformFeeRate: PLATFORM_FEE_RATE,
    platformFeeAmount,

    merchantBaseAmount,

    merchantTip: '',

    merchantOwnerRate: toNumber(ownerRate),
    merchantOwnerCommission: ownerCommission,

    merchantStaffRate: toNumber(staffRate),
    merchantStaffCommission: staffCommission,

    merchantRealAmount,
    merchantDisplayAmount
  }
}

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

    merchantBaseAmount: snapshot.merchantBaseAmount,
    merchantRealAmount: snapshot.merchantRealAmount,
    merchantDisplayAmount: snapshot.merchantDisplayAmount,

    merchantTip: snapshot.merchantTip,

    merchantOwnerRate: snapshot.merchantOwnerRate,
    merchantOwnerCommission: snapshot.merchantOwnerCommission,
    merchantStaffRate: snapshot.merchantStaffRate,
    merchantStaffCommission: snapshot.merchantStaffCommission
  }
}

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

export function getMerchantOrderAmountView(order) {
  return {
    merchantBaseAmount: order.selectedMerchantBaseAmount || 0,
    merchantRealAmount: order.selectedMerchantRealAmount || 0,
    merchantDisplayAmount: order.selectedMerchantDisplayAmount || 0,
    merchantTip: order.merchantTip || '',

    merchantOwnerCommission: order.selectedMerchantOwnerCommission || 0,
    merchantStaffCommission: order.selectedMerchantStaffCommission || 0
  }
}

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

function roundMoney(value) {
  const num = toNumber(value)

  return Math.round(num * 100) / 100
}