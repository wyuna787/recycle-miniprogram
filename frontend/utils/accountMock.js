const STORAGE_KEY = 'accountApplyMockStateV2'

const initialState = {
  accounts: [
    {
      id: 1,
      phone: '30001',
      password: '111',
      nickname: '平台管理员',
      role: 'platform_admin',
      company_type: 'platform',
      company_id: 0,
      company_name: '平台',
      status: 'approved',
      created_at: getNowText(),
      approved_at: getNowText(),
      reject_reason: ''
    }
  ],

  merchantCompanies: [
    {
      id: 1,
      name: '商家公司A',
      employee_limit: 20
    },
    {
      id: 2,
      name: '商家公司B',
      employee_limit: 20
    },
    {
      id: 3,
      name: '商家公司C',
      employee_limit: 20
    },
    {
      id: 4,
      name: '商家公司D',
      employee_limit: 40
    },
    {
      id: 5,
      name: '商家公司E',
      employee_limit: 40
    }
  ],

  recyclerCompanies: [
    {
      id: 1,
      name: '回收商A',
      code: 'A',
      employee_limit: 20
    },
    {
      id: 2,
      name: '回收商B',
      code: 'B',
      employee_limit: 20
    },
    {
      id: 3,
      name: '回收商C',
      code: 'C',
      employee_limit: 20
    },
    {
      id: 4,
      name: '回收商D',
      code: 'D',
      employee_limit: 40
    },
    {
      id: 5,
      name: '回收商E',
      code: 'E',
      employee_limit: 40
    }
  ]
}

export function getAccountState() {
  const cache = uni.getStorageSync(STORAGE_KEY)

  if (cache) {
    return cache
  }

  uni.setStorageSync(STORAGE_KEY, initialState)
  return initialState
}

export function saveAccountState(state) {
  uni.setStorageSync(STORAGE_KEY, state)
}

export function resetAccountState() {
  uni.setStorageSync(STORAGE_KEY, initialState)
  return initialState
}

export function registerAccount(data) {
  const state = getAccountState()

  const existedPhone = state.accounts.find(item => item.phone === data.phone)

  if (existedPhone) {
    return {
      ok: false,
      message: '该手机号已注册，请直接登录'
    }
  }

  if (isStaffRole(data.role)) {
    const limitResult = checkEmployeeLimit(state, data.company_type, data.company_id)

    if (!limitResult.ok) {
      return limitResult
    }
  }

  const company = getCompanyById(state, data.company_type, data.company_id)

  const account = {
    id: Date.now(),
    phone: data.phone,
    password: data.password,
    nickname: data.nickname,
    role: data.role,
    company_type: data.company_type,
    company_id: data.company_id,
    company_name: data.role === 'platform_admin' ? '平台' : company.name,
    status: 'pending',
    created_at: getNowText(),
    approved_at: '',
    reject_reason: '',
    apply_reason: data.apply_reason || ''
  }

  state.accounts.unshift(account)
  saveAccountState(state)

  return {
    ok: true,
    message: '注册成功，等待平台管理员审核'
  }
}

export function loginAccount(phone, password) {
  const state = getAccountState()
  const account = state.accounts.find(item => item.phone === phone)

  if (!account) {
    return {
      ok: false,
      message: '账号不存在，请先注册'
    }
  }

  if (account.password !== password) {
    return {
      ok: false,
      message: '密码错误'
    }
  }

  if (account.status === 'pending') {
    return {
      ok: false,
      message: '账号待平台管理员审核'
    }
  }

  if (account.status === 'rejected') {
    const reason = (account.reject_reason || '').trim()
    return {
      ok: false,
      message: reason ? `平台管理员已驳回：${reason}` : '平台管理员已驳回'
    }
  }

  if (account.status !== 'approved') {
    return {
      ok: false,
      message: '账号状态异常，请联系管理员'
    }
  }

  return {
    ok: true,
    message: '登录成功',
    account
  }
}

export function approveAccount(accountId) {
  const state = getAccountState()
  const account = state.accounts.find(item => Number(item.id) === Number(accountId))

  if (!account) {
    return {
      ok: false,
      message: '账号不存在'
    }
  }

  account.status = 'approved'
  account.approved_at = getNowText()
  account.reject_reason = ''

  saveAccountState(state)

  return {
    ok: true,
    message: '审核通过'
  }
}

export function rejectAccount(accountId, reason) {
  const state = getAccountState()
  const account = state.accounts.find(item => Number(item.id) === Number(accountId))

  if (!account) {
    return {
      ok: false,
      message: '账号不存在'
    }
  }

  account.status = 'rejected'
  account.reject_reason = reason || '管理员驳回'
  account.approved_at = ''

  saveAccountState(state)

  return {
    ok: true,
    message: '已驳回'
  }
}

export function buildCurrentUser(account) {
  return {
    id: account.id,
    phone: account.phone,
    username: account.nickname,
    nickname: account.nickname,
    role: account.role,
    company_type: account.company_type,
    company_id: account.company_id,
    company_name: account.company_name,
    status: account.status,

    can_create_inquiry: account.role === 'merchant_owner' || account.role === 'merchant_staff',
    can_view_all_inquiry: account.role === 'merchant_owner',
    can_accept_quote: account.role === 'merchant_owner',
    can_manage_staff: account.role === 'merchant_owner' || account.role === 'recycler_owner',

    can_recharge: account.role === 'recycler_owner' || account.role === 'recycler_keeper',
    can_sign: account.role === 'recycler_owner' || account.role === 'recycler_keeper',
    can_view_all_orders: account.role === 'recycler_owner' || account.role === 'recycler_keeper',
    can_view_trade_data: account.role === 'recycler_owner' || account.role === 'recycler_keeper',
    can_grab_order: account.role === 'recycler_staff',
    can_quote: account.role === 'recycler_staff'
  }
}

export function roleText(role) {
  const map = {
    platform_admin: '平台管理员',
    merchant_owner: '商家老板',
    merchant_staff: '商家员工',
    recycler_owner: '回收商老板',
    recycler_keeper: '回收商库管',
    recycler_staff: '回收商员工'
  }

  return map[role] || role || '未知角色'
}

export function statusText(status) {
  const map = {
    pending: '待平台审核',
    approved: '已通过',
    rejected: '已驳回'
  }

  return map[status] || status || '-'
}

export function isOwnerRole(role) {
  return role === 'merchant_owner' ||
    role === 'recycler_owner' ||
    role === 'platform_admin'
}

export function isStaffRole(role) {
  return role === 'merchant_staff' ||
    role === 'recycler_staff' ||
    role === 'recycler_keeper'
}

function getCompanyById(state, companyType, companyId) {
  if (companyType === 'platform') {
    return {
      id: 0,
      name: '平台'
    }
  }

  const list = companyType === 'merchant'
    ? state.merchantCompanies
    : state.recyclerCompanies

  return list.find(item => Number(item.id) === Number(companyId)) || {
    id: '',
    name: ''
  }
}

function checkEmployeeLimit(state, companyType, companyId) {
  if (!companyId) {
    return {
      ok: false,
      message: '请选择所属公司'
    }
  }

  const companies = companyType === 'merchant'
    ? state.merchantCompanies
    : state.recyclerCompanies

  const company = companies.find(item => Number(item.id) === Number(companyId))

  if (!company) {
    return {
      ok: false,
      message: '公司不存在'
    }
  }

  const staffCount = state.accounts.filter(item => {
    return item.company_type === companyType &&
      Number(item.company_id) === Number(companyId) &&
      isStaffRole(item.role) &&
      item.status !== 'rejected'
  }).length

  if (staffCount >= company.employee_limit) {
    return {
      ok: false,
      message: `${company.name} 员工数量已达上限 ${company.employee_limit} 人`
    }
  }

  return {
    ok: true,
    message: '可以注册'
  }
}

function getNowText() {
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const mi = String(now.getMinutes()).padStart(2, '0')

  return `${yyyy}-${mm}-${dd} ${hh}:${mi}`
}