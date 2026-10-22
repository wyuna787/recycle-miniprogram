// P4 · 多角色统一权限体系
// 三级控制:入口(页面访问) + 数据范围(all/company/self) + 按钮(权限点)
// 6 种角色:平台管理员 / 商家老板 / 商家员工 / 回收商老板 / 回收商库管 / 回收商员工
// 说明:这是前端 mock 权限表,作为唯一事实来源。接真实后端时改为后端下发同名权限点即可。

export const ROLE = {
  PLATFORM_ADMIN: 'platform_admin',
  MERCHANT_OWNER: 'merchant_owner',
  MERCHANT_STAFF: 'merchant_staff',
  RECYCLER_OWNER: 'recycler_owner',
  RECYCLER_KEEPER: 'recycler_keeper',
  RECYCLER_STAFF: 'recycler_staff'
}

// 数据范围:全量 / 本公司 / 仅自己
export const DATA_SCOPE = {
  ALL: 'all',
  COMPANY: 'company',
  SELF: 'self'
}

// 权限点(按钮 / 操作级)
export const PERM = {
  // 商家
  CREATE_INQUIRY: 'create_inquiry',
  ACCEPT_QUOTE: 'accept_quote',
  MANAGE_STAFF: 'manage_staff',
  SET_OWN_COMMISSION: 'set_own_commission',
  VIEW_STAFF_COMMISSION: 'view_staff_commission',
  // 回收商
  GRAB_ORDER: 'grab_order',
  QUOTE: 'quote',
  QUOTE_SEARCH: 'quote_search',
  RECHARGE: 'recharge',
  SIGN: 'sign',
  // 通用
  VIEW_ANALYSIS: 'view_analysis',
  // 平台
  AUDIT_ACCOUNT: 'audit_account',
  MANAGE_FUND: 'manage_fund',
  VIEW_PLATFORM_DATA: 'view_platform_data'
}

// 角色 → { scope, perms } 配置表
const ROLE_CONFIG = {
  [ROLE.PLATFORM_ADMIN]: {
    scope: DATA_SCOPE.ALL,
    perms: [PERM.AUDIT_ACCOUNT, PERM.MANAGE_FUND, PERM.VIEW_PLATFORM_DATA, PERM.VIEW_ANALYSIS]
  },
  [ROLE.MERCHANT_OWNER]: {
    scope: DATA_SCOPE.COMPANY,
    perms: [
      PERM.CREATE_INQUIRY, PERM.ACCEPT_QUOTE, PERM.MANAGE_STAFF,
      PERM.SET_OWN_COMMISSION, PERM.VIEW_STAFF_COMMISSION, PERM.VIEW_ANALYSIS
    ]
  },
  [ROLE.MERCHANT_STAFF]: {
    scope: DATA_SCOPE.SELF,
    perms: [PERM.CREATE_INQUIRY, PERM.SET_OWN_COMMISSION, PERM.VIEW_ANALYSIS]
  },
  [ROLE.RECYCLER_OWNER]: {
    scope: DATA_SCOPE.COMPANY,
    perms: [PERM.RECHARGE, PERM.SIGN, PERM.QUOTE_SEARCH, PERM.VIEW_ANALYSIS]
  },
  [ROLE.RECYCLER_KEEPER]: {
    scope: DATA_SCOPE.COMPANY,
    perms: [PERM.RECHARGE, PERM.SIGN, PERM.QUOTE_SEARCH, PERM.VIEW_ANALYSIS]
  },
  [ROLE.RECYCLER_STAFF]: {
    scope: DATA_SCOPE.SELF,
    perms: [PERM.GRAB_ORDER, PERM.QUOTE, PERM.QUOTE_SEARCH, PERM.VIEW_ANALYSIS]
  }
}

// 页面访问表(入口级):页面路径 → 允许的角色
const PAGE_ACCESS = {
  '/pages/merchant/device/device': [ROLE.MERCHANT_OWNER, ROLE.MERCHANT_STAFF],
  '/pages/merchant/inquiry/inquiry': [ROLE.MERCHANT_OWNER, ROLE.MERCHANT_STAFF],
  '/pages/merchant/order/order': [ROLE.MERCHANT_OWNER, ROLE.MERCHANT_STAFF],
  '/pages/merchant/auth/auth': [ROLE.MERCHANT_OWNER],
  '/pages/company/staff-list/staff-list': [ROLE.MERCHANT_OWNER, ROLE.RECYCLER_OWNER],
  '/pages/merchant/commission/commission': [ROLE.MERCHANT_OWNER, ROLE.MERCHANT_STAFF],
  '/pages/merchant/analysis/analysis': [ROLE.MERCHANT_OWNER, ROLE.MERCHANT_STAFF],

  '/pages/recycler/inquiry/inquiry': [ROLE.RECYCLER_OWNER, ROLE.RECYCLER_KEEPER, ROLE.RECYCLER_STAFF],
  '/pages/recycler/order/order': [ROLE.RECYCLER_OWNER, ROLE.RECYCLER_KEEPER, ROLE.RECYCLER_STAFF],
  '/pages/recycler/settlement/settlement': [ROLE.RECYCLER_OWNER, ROLE.RECYCLER_KEEPER],
  '/pages/recycler/quote-search/quote-search': [ROLE.RECYCLER_OWNER, ROLE.RECYCLER_KEEPER, ROLE.RECYCLER_STAFF],
  '/pages/recycler/analysis/analysis': [ROLE.RECYCLER_OWNER, ROLE.RECYCLER_KEEPER, ROLE.RECYCLER_STAFF],

  '/pages/platform/payment/payment': [ROLE.PLATFORM_ADMIN],
  '/pages/platform/orders/orders': [ROLE.PLATFORM_ADMIN],
  '/pages/platform/fund/fund': [ROLE.PLATFORM_ADMIN],
  '/pages/platform/dashboard/dashboard': [ROLE.PLATFORM_ADMIN],
  '/pages/platform/finance/finance': [ROLE.PLATFORM_ADMIN],
  '/pages/platform/payout/payout': [ROLE.PLATFORM_ADMIN]
}

function getRole(user) {
  return (user && user.role) || ''
}

// 是否拥有某权限点(按钮级)
export function hasPermission(user, perm) {
  const cfg = ROLE_CONFIG[getRole(user)]
  if (!cfg) return false
  return cfg.perms.includes(perm)
}

// 数据范围(列表过滤用)
export function getDataScope(user) {
  const cfg = ROLE_CONFIG[getRole(user)]
  return cfg ? cfg.scope : DATA_SCOPE.SELF
}

// 是否可访问某页面(入口级)。未在表中登记的页面默认放行(公共页)。
export function canAccessPage(user, pagePath) {
  if (!pagePath) return true
  const key = pagePath.split('?')[0]
  const allow = PAGE_ACCESS[key]
  if (!allow) return true
  return allow.includes(getRole(user))
}

// 页面守卫:无权访问则提示并返回。返回 true 表示允许继续。
// 用法:onShow 内 if (!guardPage(currentUser.value, '/pages/xxx')) return
export function guardPage(user, pagePath) {
  if (canAccessPage(user, pagePath)) return true

  uni.showToast({ title: '无访问权限', icon: 'none' })
  setTimeout(() => uni.navigateBack(), 600)
  return false
}

export function getCurrentUser() {
  return uni.getStorageSync('currentUser') || uni.getStorageSync('userInfo') || {}
}
