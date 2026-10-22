import { get, post } from '@/utils/request.js'

export function createDevice(data) {
  return post('/api/devices', data)
}

export function getMyInquiries() {
  return get('/api/inquiries/my')
}

export function getRecyclerInquiries() {
  return get('/api/inquiries/recycler')
}

export function createQuote(data) {
  return post('/api/quotes', data)
}

export function getMyQuotes() {
  return get('/api/quotes/my')
}

export function getQuotesByInquiry(inquiryId) {
  return get(`/api/quotes/by-inquiry/${inquiryId}`)
}

export function acceptQuote(quoteId) {
  return post(`/api/quotes/${quoteId}/accept`)
}

export function getAdminTrades() {
  return get('/api/admin/trades')
}

export function getMyOrders() {
  return get('/api/orders/my')
}

export function getOrderDetail(orderId) {
  return get(`/api/orders/${orderId}`)
}

export function shipOrder(orderId, data) {
  return post(`/api/orders/${orderId}/ship`, data)
}

export function receiveOrder(orderId) {
  return post(`/api/orders/${orderId}/receive`)
}

export function inspectOrder(orderId, data) {
  return post(`/api/orders/${orderId}/inspect`, data)
}

export function confirmOrder(orderId, data = {}) {
  return post(`/api/orders/${orderId}/confirm`, data)
}

export function appealOrder(orderId, data) {
  return post(`/api/orders/${orderId}/appeal`, data)
}

export function closeAdminOrder(orderId, data) {
  return post(`/api/admin/orders/${orderId}/close`, data)
}

export function lookupCompanyQuotes(number) {
  return get('/api/quotes/lookup', { number })
}
