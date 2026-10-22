// 资金池状态机(P1):冻结 / 释放 / 扣款 / 流水
// 资金状态:未占用 unoccupied → 已冻结 frozen → 已扣款 deducted / 已释放 released
// 注意:这里是平台内部记账,不是银行自动转账。

import { getNowText } from './tradeFlow.js'
import { calcPlatformFee } from './moneyMock.js'

const FUND_KEY = 'recyclerFundPoolList'
const FLOW_KEY = 'recyclerFundFlowList'

export const FUND_STATUS = {
  UNOCCUPIED: 'unoccupied',
  FROZEN: 'frozen',
  DEDUCTED: 'deducted',
  RELEASED: 'released'
}

export const FLOW_TYPE = {
  RECHARGE: 'recharge',        // 充值入账
  FREEZE: 'freeze',            // 报价/成交冻结
  RELEASE: 'release',          // 取消/放弃/关闭释放
  DEDUCT: 'deduct',            // 成交扣款
  PLATFORM_FEE: 'platform_fee' // 平台服务费
}

const FLOW_TYPE_TEXT = {
  recharge: '充值入账',
  manual_deduct:'人工扣除',
  merchant_recharge:'商家充值',
  merchant_refund:'商家退款',
  freeze: '报价冻结',
  release: '释放冻结',
  deduct: '成交扣款',
  platform_fee: '平台收入'
}

export function getFlowTypeText(type) {
  return FLOW_TYPE_TEXT[type] || type || '-'
}

function num(v) {
  return Number(v || 0)
}

export function loadFunds() {
  return uni.getStorageSync(FUND_KEY) || []
}

function saveFunds(list) {
  uni.setStorageSync(FUND_KEY, list)
}

export function loadFlows() {
  return uni.getStorageSync(FLOW_KEY) || []
}

function saveFlows(list) {
  uni.setStorageSync(FLOW_KEY, list)
}

// 取某公司资金账户(总余额 / 冻结 / 已扣款),可用余额 = 总余额 - 冻结
export function getFund(companyId) {
  const id = Number(companyId)
  const fund = loadFunds().find(item => Number(item.companyId) === id)

  const base = fund || {
    companyId: id,
    companyName: '',
    balance: 0,
    frozenAmount: 0,
    deductedAmount: 0
  }

  return {
    ...base,
    balance: num(base.balance),
    frozenAmount: num(base.frozenAmount),
    deductedAmount: num(base.deductedAmount),
    availableAmount: num(base.balance) - num(base.frozenAmount)
  }
}

export function getAvailable(companyId) {
  return getFund(companyId).availableAmount
}

function writeFund(companyId, mutate) {
  const list = loadFunds()
  const id = Number(companyId)
  let fund = list.find(item => Number(item.companyId) === id)

  if (!fund) {
    fund = { companyId: id, companyName: '', balance: 0, frozenAmount: 0, deductedAmount: 0 }
    list.unshift(fund)
  }

  fund.balance = num(fund.balance)
  fund.frozenAmount = num(fund.frozenAmount)
  fund.deductedAmount = num(fund.deductedAmount)

  mutate(fund)

  fund.updatedTime = getNowText()
  saveFunds(list)
  return fund
}

function addFlow(flow) {
  const list = loadFlows()
  list.unshift({
    id: `flow_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    time: getNowText(),
    status: 'success',
    ...flow
  })
  saveFlows(list)
}

// 冻结:商家确认成交时调用。可用余额不足返回 { ok:false }
export function freezeFund(companyId, amount, ctx = {}) {
  const value = num(amount)
  if (value <= 0) return { ok: false, msg: '冻结金额不正确' }

  const available = getAvailable(companyId)
  if (value > available) {
    return { ok: false, msg: `可用余额不足,当前可用 ¥${available.toFixed(2)}` }
  }

  writeFund(companyId, fund => { fund.frozenAmount += value })

  addFlow({
    type: FLOW_TYPE.FREEZE,
    companyId: Number(companyId),
    orderNo: ctx.orderNo || '',
    merchantId: ctx.merchantId || '',
    operator: ctx.operator || '',
    amount: value,
    remark: ctx.remark || '商家确认成交,冻结对应额度'
  })

  return { ok: true }
}

// 释放:取消成交 / 放弃报价 / 订单关闭时调用
export function releaseFund(companyId, amount, ctx = {}) {
  const value = num(amount)
  if (value <= 0) return { ok: false, msg: '释放金额不正确' }

  writeFund(companyId, fund => {
    fund.frozenAmount = Math.max(0, fund.frozenAmount - value)
  })

  addFlow({
    type: FLOW_TYPE.RELEASE,
    companyId: Number(companyId),
    orderNo: ctx.orderNo || '',
    operator: ctx.operator || '',
    amount: value,
    remark: ctx.remark || '订单取消/关闭,释放冻结额度'
  })

  return { ok: true }
}

// 扣款:商家上传发货后调用。冻结转已扣款,并生成平台服务费流水
export function deductFund(companyId, amount, ctx = {}) {
  const value = num(amount)
  if (value <= 0) return { ok: false, msg: '扣款金额不正确' }

  writeFund(companyId, fund => {
    fund.frozenAmount = Math.max(0, fund.frozenAmount - value)
    fund.balance = Math.max(0, fund.balance - value)
    fund.deductedAmount += value
  })

  addFlow({
    type: FLOW_TYPE.DEDUCT,
    companyId: Number(companyId),
    orderNo: ctx.orderNo || '',
    operator: ctx.operator || '',
    amount: value,
    remark: ctx.remark || '商家已发货,冻结金额转扣款'
  })

  const platformFee = calcPlatformFee(value)
  if (platformFee > 0) {
    addFlow({
      type: FLOW_TYPE.PLATFORM_FEE,
      companyId: Number(companyId),
      orderNo: ctx.orderNo || '',
      amount: platformFee,
      remark: '平台收入'
    })
  }

  return { ok: true, platformFee }
}

// 充值流水补登:充值审核通过时调用(余额已在审核处加好,这里只补记一条流水)
// 不改余额,避免与审核处的余额累加重复计算。
export function recordRechargeFlow(companyId, amount, ctx = {}) {
  const value = num(amount)
  if (value <= 0) return { ok: false, msg: '充值金额不正确' }

  addFlow({
    type: FLOW_TYPE.RECHARGE,
    companyId: Number(companyId),
    operator: ctx.operator || '',
    amount: value,
    remark: ctx.remark || '充值审核通过,额度入账'
  })

  return { ok: true }
}

// 订单终止(取消/关闭)统一释放:仅当订单仍处于冻结(未扣款)状态时释放,
// 并回写订单的资金状态,避免重复释放。target 为 inquiryList 中的订单对象。
export function releaseIfFrozen(target, ctx = {}) {
  if (!target || target.fundStatus !== FUND_STATUS.FROZEN) {
    return { ok: false, released: false }
  }

  const releaseAmount = num(
    target.fundFrozenAmount ||
    target.selectedRecyclerQuoteAmount ||
    target.selectedAmount ||
    0
  )

  const res = releaseFund(target.selectedRecyclerCompanyId, releaseAmount, ctx)

  if (res.ok) {
    target.fundStatus = FUND_STATUS.RELEASED
    target.quotaStatus = 'released'
    target.quotaReleaseTime = getNowText()
  }

  return { ...res, released: res.ok, releaseAmount }
}

export function getCompanyFlows(companyId) {
  const id = Number(companyId)
  return loadFlows().filter(item => Number(item.companyId) === id)
}
