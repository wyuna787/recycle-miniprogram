/**
 * 交易主流程状态与工具（MVP 前端闭环，不含资金池/抽成）
 */

export const QUOTE_STATUS = {
  PENDING_QUOTE: 'pending_quote',
  QUOTED: 'quoted',
  ACCEPTED: 'accepted',
  EXPIRED: 'expired',
  OFF_SHELF: 'off_shelf',
  DONE: 'done',
  CANCELLED: 'cancelled'
}

export const TRADE_STATUS = {
  CONFIRMED: 'confirmed',
  SHIPPED: 'shipped',
  RECEIVED: 'received',
  INSPECTION_DONE: 'inspection_done',
  COMPLETED: 'completed',
  CLOSED: 'closed',
  APPEALING: 'appealing',
  CANCELLED: 'cancelled'
}

const LEGACY_TRADE_MAP = {
  waiting_merchant_ship: TRADE_STATUS.CONFIRMED,
  waiting_recycler_payment: TRADE_STATUS.CONFIRMED,
  payment_reviewing: TRADE_STATUS.CONFIRMED,
  payment_rejected: TRADE_STATUS.CONFIRMED,
  merchant_shipped: TRADE_STATUS.SHIPPED,
  recycler_received: TRADE_STATUS.INSPECTION_DONE,
  platform_paid: TRADE_STATUS.COMPLETED
}

const TRADE_FLOW_STATUS_LABELS = {
  expired: '报价已结束',
  pending_quote: '待报价',
  quoted: '已报价，待商家确认',
  confirmed: '待发货',
  shipped: '商家已发货，待验机',
  received: '商家已发货，待验机',
  inspection_done: '验机通过，待商家确认结算',
  completed: '已完成',
  appealing: '申诉中',
  closed: '已关闭',
  cancelled: '已取消',
  waiting_merchant_ship: '已确认，待商家发货',
  waiting_recycler_payment: '已确认，待商家发货',
  payment_reviewing: '已确认，待商家发货',
  payment_rejected: '已确认，待商家发货',
  merchant_shipped: '商家已发货，待验机',
  recycler_received: '验机通过，待商家确认结算',
  platform_paid: '已完成'
}

// 回收商视角独立文案
export const RECYCLER_STATUS_LABELS = {
  expired: '报价已结束',
  pending_quote: '待报价',
  quoted: '已报价，待商家确认',
  confirmed: '待发货',
  shipped: '商家已发货，待验机',
  received: '商家已发货，待验机',
  inspection_done: '验机通过，待结算',
  completed: '已完成',
  appealing: '申诉中',
  closed: '已关闭',
  cancelled: '已取消',
  merchant_shipped: '商家已发货，待验机',
  recycler_received: '验机通过，待结算',
  platform_paid: '已完成'
}

export function getRecyclerTradeFlowStatusLabel(status) {
  if (!status) return '-'
  const normalized = normalizeTradeStatus(status)
  return RECYCLER_STATUS_LABELS[normalized] || RECYCLER_STATUS_LABELS[status] || getTradeFlowStatusLabel(status)
}

export function normalizeTradeStatus(status) {
  if (!status) return ''
  return LEGACY_TRADE_MAP[status] || status
}

export function getTradeFlowStatusLabel(status) {
  if (!status) return '-'
  const normalized = normalizeTradeStatus(status)
  return TRADE_FLOW_STATUS_LABELS[normalized] || TRADE_FLOW_STATUS_LABELS[status] || status
}

export function getTradeFlowStatusClassName(status) {
  const normalized = normalizeTradeStatus(status)

  if (normalized === TRADE_STATUS.CONFIRMED) return 'cancel'

  if (normalized === TRADE_STATUS.COMPLETED || normalized === 'platform_paid') {
    return 'success'
  }

  if (normalized === TRADE_STATUS.APPEALING) {
    return 'cancel'
  }

  if (normalized === TRADE_STATUS.CLOSED || normalized === TRADE_STATUS.CANCELLED) {
    return 'off'
  }

  if (normalized === 'pending_quote' || normalized === 'quoted' || normalized === TRADE_STATUS.CONFIRMED) {
    return 'waiting'
  }

  return 'processing'
}

export function resolveItemTradeStatus(item) {
  if (!item) return ''

  if (item.order?.status) {
    return normalizeTradeStatus(item.order.status)
  }

  const raw = item.tradeStatus || item.trade_status || item.status || ''

  // 已进入发货及之后阶段的订单，优先用其真实状态，避免被"已接单→confirmed"误盖
  const normalizedRaw = normalizeTradeStatus(raw)
  if ([
    TRADE_STATUS.SHIPPED,
    TRADE_STATUS.RECEIVED,
    TRADE_STATUS.INSPECTION_DONE,
    TRADE_STATUS.COMPLETED,
    TRADE_STATUS.APPEALING,
    TRADE_STATUS.CLOSED
  ].includes(normalizedRaw)) {
    return normalizedRaw
  }

  if (raw === '商家已接单' || item.quoteStatus === QUOTE_STATUS.ACCEPTED) {
    return TRADE_STATUS.CONFIRMED
  }

  if (raw === '交易完成' || raw === 'platform_paid') {
    return TRADE_STATUS.COMPLETED
  }

  if (raw === '订单已取消') {
    return TRADE_STATUS.CANCELLED
  }

  if (raw === 'quoted' || raw === '已有回收商报价') {
    return 'quoted'
  }

  if (raw === 'pending_quote' || raw === '待报价' || item.quoteStatus === QUOTE_STATUS.PENDING_QUOTE) {
    return 'pending_quote'
  }

  if (Array.isArray(item.quotes) && item.quotes.length > 0 && !isOrderTrade(item)) {
    return 'quoted'
  }

  return normalizeTradeStatus(raw)
}

export function getTradeStatus(item) {
  const raw = item?.tradeStatus || ''
  return LEGACY_TRADE_MAP[raw] || raw
}

export function isTradeStatus(item, ...statuses) {
  // 支持两种写法：isTradeStatus(item, a, b, c) 或 isTradeStatus(item, [a, b, c])
  const list = (statuses.length === 1 && Array.isArray(statuses[0])) ? statuses[0] : statuses
  const current = getTradeStatus(item)
  const raw = item?.tradeStatus || ''

  return list.some(s => {
    return current === s || raw === s || LEGACY_TRADE_MAP[raw] === s || LEGACY_TRADE_MAP[s] === current
  })
}

export function isOrderTrade(item) {
  return !!item?.tradeStatus ||
    item?.quoteStatus === QUOTE_STATUS.ACCEPTED ||
    item?.status === '商家已接单'
}

export function isPendingQuote(item) {
  const qs = item?.quoteStatus
  return qs === QUOTE_STATUS.PENDING_QUOTE ||
    qs === 'waiting_quote' ||
    (!qs && (item?.status === '待报价' || item?.status === 'pending_quote'))
}

export function isQuotedInquiry(item) {
  return item?.quoteStatus === QUOTE_STATUS.QUOTED ||
    (Array.isArray(item?.quotes) && item.quotes.length > 0 && !isOrderTrade(item))
}

export function normalizeInquiryItem(item) {
  if (!item) return item

  if (item.quoteStatus === 'waiting_quote') {
    item.quoteStatus = QUOTE_STATUS.PENDING_QUOTE
  }

  return item
}

export function normalizeInquiryList(list) {
  return (list || []).map(item => normalizeInquiryItem({
    ...item,
    quotes: Array.isArray(item.quotes) ? item.quotes : []
  }))
}

export function generateOrderNo() {
  return `DD${Date.now()}`
}

export function getNowText() {
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const mi = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')

  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

export function getQuoteValidUntil(days = 1) {
  const now = new Date()
  now.setDate(now.getDate() + Number(days || 1))
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')

  return `${yyyy}-${mm}-${dd} 23:59:59`
}

export function isInquiryVisibleToRecycler(inquiry, user) {
  if (!inquiry || !user) return false

  const role = user.role

  if (role !== 'recycler_owner' &&
    role !== 'recycler_keeper' &&
    role !== 'recycler_staff') {
    return false
  }

  const companyId = Number(user.company_id)

  if (!companyId) return false

  const targetIds = inquiry.targetRecyclerIds || inquiry.recyclerCompanyIds || []

  if (Array.isArray(targetIds) && targetIds.length > 0) {
    return targetIds.some(id => Number(id) === companyId)
  }

  return true
}

export function markOtherQuotesExpired(inquiry, selectedQuoteId) {
  const quotes = Array.isArray(inquiry.quotes) ? inquiry.quotes : []

  quotes.forEach(quote => {
    if (Number(quote.id) !== Number(selectedQuoteId)) {
      quote.quoteStatus = QUOTE_STATUS.EXPIRED
    } else {
      quote.quoteStatus = QUOTE_STATUS.ACCEPTED
    }
  })
}

export function getDeviceTitle(item) {
  const brand = item?.brand || ''
  const model = item?.model || ''
  const name = item?.device_name || ''

  if (brand || model) {
    return `${brand} ${model}`.trim()
  }

  return name || '未知设备'
}

// 任意端口跳转到统一的「设备详细信息」页面:把当前条目暂存到本地，详情页读取
export function openDeviceDetail(item) {
  try {
    uni.setStorageSync('deviceDetailItem', item || {})
  } catch (e) {
    // ignore
  }

  uni.navigateTo({
    url: '/pages/common/device-detail/device-detail'
  })
}

export function getTradeStatusText(item) {
  if (item?.cancelApplyStatus === 'pending') {
    return { text: '取消审核中', className: 'cancel' }
  }

  if (isTradeStatus(item, TRADE_STATUS.CANCELLED) || item?.quoteStatus === QUOTE_STATUS.CANCELLED) {
    return { text: '已取消', className: 'off' }
  }

  const status = resolveItemTradeStatus(item)

  return {
    text: getTradeFlowStatusLabel(status),
    className: getTradeFlowStatusClassName(status)
  }
}

export function getRecyclerTradeStatusText(item) {
  if (item?.cancelApplyStatus === 'pending') {
    return { text: '取消审核中', className: 'cancel' }
  }

  if (isTradeStatus(item, TRADE_STATUS.CANCELLED) || item?.quoteStatus === QUOTE_STATUS.CANCELLED) {
    return { text: '已取消', className: 'off' }
  }

  const status = resolveItemTradeStatus(item)

  return {
    text: getRecyclerTradeFlowStatusLabel(status),
    className: getTradeFlowStatusClassName(status)
  }
}

export function getInspectionResultText(result) {
  const map = {
    pass: '验机通过',
    adjust: '验机调价',
    return: '验机退货',
    reject: '验机退货'
  }

  return map[result] || '-'
}

export function loadInquiryList() {
  return normalizeInquiryList(uni.getStorageSync('inquiryList') || [])
}

export function saveInquiryList(list) {
  uni.setStorageSync('inquiryList', list)
}

export function getOrderStatusLabel(status) {
  return getTradeFlowStatusLabel(status)
}

export function getAdminTradeStatusLabel(status) {
  return getTradeFlowStatusLabel(status)
}

export function getAdminTradeStatus(item) {
  return resolveItemTradeStatus(item) ||
    item?.tradeStatus ||
    item?.trade_status ||
    item?.status ||
    item?.order?.status ||
    ''
}

export function mapOrderLifecycleFields(order = {}) {
  return {
    merchantConfirmTime: order.merchant_confirm_time || order.merchantConfirmTime || '',
    merchant_confirm_time: order.merchant_confirm_time || order.merchantConfirmTime || '',
    appealReason: order.appeal_reason || order.appealReason || '',
    appeal_reason: order.appeal_reason || order.appealReason || '',
    appealTime: order.appeal_time || order.appealTime || '',
    appeal_time: order.appeal_time || order.appealTime || '',
    closeReason: order.close_reason || order.closeReason || '',
    close_reason: order.close_reason || order.closeReason || '',
    closeTime: order.close_time || order.closeTime || '',
    close_time: order.close_time || order.closeTime || ''
  }
}

export function mapOrderInspectionFields(order = {}) {
  const inspectionType = order.inspection_type || order.inspectionType || ''

  return {
    inspection_type: inspectionType,
    inspectionType,
    inspectionResult: inspectionType === 'reject' ? 'return' : inspectionType,
    inspectionAdjustPrice: order.inspection_price ?? order.inspectionPrice ?? '',
    inspection_price: order.inspection_price ?? order.inspectionPrice ?? null,
    inspectionPrice: order.inspection_price ?? order.inspectionPrice ?? null,
    inspectionReason: order.inspection_reason || order.inspectionReason || '',
    inspection_reason: order.inspection_reason || order.inspectionReason || '',
    inspectionTime: order.inspection_time || order.inspectionTime || '',
    inspection_time: order.inspection_time || order.inspectionTime || ''
  }
}

export function mapOrderFields(order = {}) {
  const status = normalizeTradeStatus(order.status || order.trade_status || order.tradeStatus || '')

  return {
    ...order,
    orderNo: order.order_no || order.orderNo || order.no || '',
    order_no: order.order_no || order.orderNo || order.no || '',
    no: order.order_no || order.orderNo || order.no || '',
    status,
    tradeStatus: status,
    expressCompany: order.express_company || order.expressCompany || '',
    expressNo: order.tracking_no || order.trackingNo || order.express_no || order.expressNo || '',
    trackingNo: order.tracking_no || order.trackingNo || '',
    merchantShipTime: order.ship_time || order.shipTime || '',
    ship_time: order.ship_time || order.shipTime || '',
    recyclerReceiveTime: order.receive_time || order.receiveTime || '',
    receiveTime: order.receive_time || order.receiveTime || '',
    ...mapOrderInspectionFields(order),
    ...mapOrderLifecycleFields(order)
  }
}

export function normalizeAdminTrade(item) {
  if (!item) return item

  const device = item.device || {}
  const merchant = item.merchant || {}
  const order = item.order || null
  const quotes = Array.isArray(item.quotes) ? item.quotes : []
  const tradeStatus = getAdminTradeStatus(item)
  const prices = quotes
    .map(quote => Number(quote.price))
    .filter(price => !Number.isNaN(price) && price > 0)

  const minQuotePrice = prices.length ? Math.min(...prices) : null
  const maxQuotePrice = prices.length ? Math.max(...prices) : null

  let selectedRecyclerCompanyName = item.selectedRecyclerCompanyName || '-'

  if (order?.recycler_company_name) {
    selectedRecyclerCompanyName = order.recycler_company_name
  } else if (order?.recyclerCompanyName) {
    selectedRecyclerCompanyName = order.recyclerCompanyName
  } else if (quotes.length) {
    const acceptedQuote = quotes.find(quote => quote.status === 'accepted')
    const targetQuote = acceptedQuote || quotes[quotes.length - 1]
    selectedRecyclerCompanyName = targetQuote.recycler_company_name ||
      targetQuote.recyclerCompanyName ||
      targetQuote.recycler_name ||
      '-'
  }

  return {
    ...item,
    id: item.id || item.inquiry_id,
    inquiry_id: item.inquiry_id || item.id,
    tradeStatus,
    status: tradeStatus,
    brand: item.brand || device.brand || '',
    model: item.model || device.model || '',
    merchantCompanyName: item.merchantCompanyName ||
      merchant.company_name ||
      merchant.name ||
      '-',
    merchantPhone: item.merchantPhone || merchant.phone || '',
    selectedRecyclerCompanyName,
    selectedAmount: order?.price || item.selectedAmount || 0,
    quoteCount: item.quoteCount ?? quotes.length,
    minQuotePrice: item.minQuotePrice ?? minQuotePrice,
    maxQuotePrice: item.maxQuotePrice ?? maxQuotePrice,
    orderNo: order?.order_no || order?.orderNo || item.orderNo || '',
    order,
    quotes,
    createTime: item.createTime || item.created_at || '-',
    expressCompany: order?.express_company || order?.expressCompany || item.expressCompany || '',
    expressNo: order?.tracking_no || order?.trackingNo || item.expressNo || '',
    shipTime: order?.ship_time || order?.shipTime || '',
    receiveTime: order?.receive_time || order?.receiveTime || '',
    ...mapOrderInspectionFields(order || {}),
    ...mapOrderLifecycleFields(order || {})
  }
}

export function normalizeAdminTradeList(res) {
  const list = Array.isArray(res)
    ? res
    : (res?.list || res?.items || res?.data || [])

  return list.map(item => normalizeAdminTrade(item))
}

export function ordersToAdminTradeFallback(res) {
  const orders = normalizeBackendOrderList(res)

  return orders.map(order => ({
    id: order.inquiry_id || order.id,
    inquiry_id: order.inquiry_id || order.id,
    device_id: order.device_id,
    merchant_id: order.merchant_id,
    tradeStatus: order.status,
    status: order.status,
    trade_status: order.status,
    brand: order.brand,
    model: order.model,
    merchantCompanyName: order.merchantCompanyName,
    merchantPhone: '',
    selectedRecyclerCompanyName: order.selectedRecyclerCompanyName,
    selectedAmount: order.selectedAmount,
    quoteCount: 0,
    minQuotePrice: null,
    maxQuotePrice: null,
    orderNo: order.orderNo,
    order: {
      id: order.id,
      order_no: order.orderNo,
      orderNo: order.orderNo,
      status: order.status,
      price: order.selectedAmount,
      express_company: order.expressCompany,
      tracking_no: order.expressNo,
      expressCompany: order.expressCompany,
      trackingNo: order.expressNo,
      merchant_confirm_time: order.merchant_confirm_time || order.merchantConfirmTime || '',
      merchantConfirmTime: order.merchant_confirm_time || order.merchantConfirmTime || '',
      appeal_reason: order.appeal_reason || order.appealReason || '',
      appealReason: order.appeal_reason || order.appealReason || '',
      appeal_time: order.appeal_time || order.appealTime || '',
      appealTime: order.appeal_time || order.appealTime || '',
      close_reason: order.close_reason || order.closeReason || '',
      closeReason: order.close_reason || order.closeReason || '',
      close_time: order.close_time || order.closeTime || '',
      closeTime: order.close_time || order.closeTime || ''
    },
    quotes: [],
    device: {
      brand: order.brand,
      model: order.model
    },
    merchant: {
      company_name: order.merchantCompanyName
    },
    createTime: order.createTime,
    created_at: order.createTime,
    expressCompany: order.expressCompany,
    expressNo: order.expressNo
  }))
}

export function normalizeBackendOrder(item) {
  if (!item) return item

  const mapped = mapOrderFields(item)
  const device = item.device || {}
  const merchant = item.merchant || {}
  const recycler = item.recycler || {}
  const quote = item.quote || {}

  return {
    ...item,
    ...mapped,
    id: item.id,
    merchantCompanyName: item.merchant_company_name ||
      item.merchantCompanyName ||
      merchant.company_name ||
      merchant.name ||
      item.merchant_name ||
      '-',
    selectedRecyclerCompanyName: item.recycler_company_name ||
      item.recyclerCompanyName ||
      recycler.company_name ||
      recycler.name ||
      item.recycler_name ||
      '-',
    selectedAmount: item.price ||
      item.quote_amount ||
      item.quoteAmount ||
      quote.price ||
      item.amount ||
      0,
    brand: item.brand || item.device_brand || device.brand || '',
    model: item.model || item.device_model || device.model || '',
    createTime: item.create_time || item.created_at || item.createTime || '-',
    merchantAppealTime: mapped.appealTime,
    merchantAppealReason: mapped.appealReason
  }
}

export function normalizeBackendOrderList(res) {
  const list = Array.isArray(res)
    ? res
    : (res?.list || res?.items || res?.data || [])

  return list.map(item => normalizeBackendOrder(item))
}

export function findInquiryById(list, id) {
  return list.find(item => Number(item.id) === Number(id))
}
