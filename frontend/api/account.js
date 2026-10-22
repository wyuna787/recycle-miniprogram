import { get, post } from '@/utils/request.js'

export function getCompanies() {
  return get('/api/account/companies')
}

export function register(data) {
  return post('/api/account/register', data)
}

export function login(data) {
  return post('/api/account/login', data)
}

export function getCurrentUser() {
  return get('/api/account/me')
}

export function changePassword(data) {
  return post('/api/account/change-password', data)
}

export function getCompanyStaff() {
  return get('/api/company/staff')
}

export function getPendingAccounts() {
  return get('/api/admin/accounts/pending')
}

export function getAllAccounts(status) {
  const q = status ? `?status=${status}` : ''
  return get(`/api/admin/accounts${q}`)
}

export function approveAccount(accountId) {
  return post(`/api/admin/accounts/${accountId}/approve`)
}

export function rejectAccount(accountId, reason) {
  return post(`/api/admin/accounts/${accountId}/reject`, {
    reason
  })
}

// 清退(停用)单个账号
export function disableAccount(accountId) {
  return post(`/api/admin/accounts/${accountId}/disable`)
}

// 恢复被清退/驳回的账号
export function enableAccount(accountId) {
  return post(`/api/admin/accounts/${accountId}/enable`)
}

// 清退整个公司(老板+员工)
export function disableCompany(companyType, companyId) {
  return post(`/api/admin/company/${companyType}/${companyId}/disable`)
}

export function manageCompanyStaff(id, action) { return post(`/api/company/staff/${id}/${action}`) }

export function addCompanyStaff(data) { return post("/api/company/staff", data) }
