import { get, post } from '@/utils/request.js'

// ───────── 资金池 ─────────
export function getAdminFundPools() {
  return get('/api/admin/fund/pools')
}

export function setFundBalance(companyId, balance) {
  return post(`/api/admin/fund/pools/${companyId}/set`, { balance })
}

export function getFundPool(companyId) {
  return get(`/api/fund/pool/${companyId}`)
}

// ───────── 资金流水 ─────────
export function getFundFlows(companyId) {
  return get('/api/fund/flows', { company_id: companyId })
}

export function getAdminFundFlows(params = {}) {
  return get('/api/admin/fund/flows', params)
}

// ───────── 充值申请 ─────────
export function applyRecharge(data) {
  return post('/api/recharge/apply', data)
}

export function getRechargeApplies(params = {}) {
  return get('/api/recharge/applies', params)
}

export function approveRecharge(applyId) {
  return post(`/api/admin/recharge/${applyId}/approve`)
}

export function rejectRecharge(applyId, reason) {
  return post(`/api/admin/recharge/${applyId}/reject`, { reason })
}

// ───────── 取消订单审核 ─────────
export function cancelApplyOrder(orderId, reason) {
  return post(`/api/orders/${orderId}/cancel-apply`, { reason })
}

export function approveCancelOrder(orderId) {
  return post(`/api/admin/orders/${orderId}/cancel-approve`)
}

export function rejectCancelOrder(orderId, reason) {
  return post(`/api/admin/orders/${orderId}/cancel-reject`, { reason })
}

// ───────── 抽成比例 ─────────
export function getCommissionRate(userId) {
  return get('/api/commission/rate', { user_id: userId })
}

export function getCommissionRates(companyId) {
  return get('/api/commission/rates', { company_id: companyId })
}

export function setCommissionRate(userId, rate) {
  return post('/api/commission/rate', { user_id: userId, rate })
}

export function getMerchantDeposits() { return get('/api/admin/merchant/deposits') }
export function setMerchantDeposit(id, balance) { return post(`/api/admin/merchant/${id}/deposit`, { balance }) }
