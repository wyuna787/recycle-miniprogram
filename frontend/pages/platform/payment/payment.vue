<template>
  <view class="page">
    <view class="hero">
      <view class="hero-top">
        <view class="back-btn" @click="goBack">‹</view>
        <view>
          <view class="hello">{{ currentUser.username || '平台管理员' }}</view>
          <view class="desc">审核商家、回收商及平台相关账号注册申请。</view>
        </view>
        <view class="hero-icon">审</view>
      </view>

      <view class="stats">
        <view class="stat-item">
          <view class="stat-number">{{ pendingAccountList.length }}</view>
          <view class="stat-label">账号待审</view>
        </view>

        <view class="stat-item">
          <view class="stat-number">{{ approvedAccountCount }}</view>
          <view class="stat-label">已通过</view>
        </view>

        <view class="stat-item">
          <view class="stat-number">{{ rejectedAccountCount }}</view>
          <view class="stat-label">已驳回</view>
        </view>
      </view>
    </view>

    <!-- 账号审核 -->
    <view>
      <view class="section-head">
        <view class="section-title">账号审核</view>
        <view class="section-desc">商家老板、商家员工、回收商老板、回收商员工、回收商库管、平台管理员</view>
      </view>

      <input class="order-search" v-model="accountSearch" placeholder="账号ID / 公司ID / 公司名称 / 姓名 / 手机号" />
      <!-- 状态 tab -->
      <view class="status-tabs">
        <view :class="['status-tab', accountTab==='pending'?'active':'']" @click="switchAccountTab('pending')">
          待审核 <text v-if="pendingAccountList.length" class="badge">{{ pendingAccountList.length }}</text>
        </view>
        <view :class="['status-tab', accountTab==='approved'?'active':'']" @click="switchAccountTab('approved')">
          已通过 <text v-if="approvedAccountCount" class="badge-gray">{{ approvedAccountCount }}</text>
        </view>
        <view :class="['status-tab', accountTab==='rejected'?'active':'']" @click="switchAccountTab('rejected')">
          已驳回 <text v-if="rejectedAccountCount" class="badge-gray">{{ rejectedAccountCount }}</text>
        </view>
      </view>

      <view v-if="currentAccountList.length === 0" class="empty">
        暂无账号{{ accountTab==='pending'?'待审核':accountTab==='approved'?'已通过':'已驳回' }}
      </view>

      <view
        v-for="item in currentAccountList"
        :key="item.id"
        class="card"
      >
        <view class="card-head">
          <view>
            <view class="card-title">{{ item.nickname || item.username || '未命名账号' }}</view>
            <view class="card-sub">{{ roleText(item.role) }}</view>
          </view>

          <view :class="['status-pill', item.status==='approved'?'approved':(item.status==='rejected'||item.status==='disabled')?'rejected':'waiting']">
            {{ item.status==='approved'?'已通过':item.status==='rejected'?'已驳回':item.status==='disabled'?'已清退':'待审核' }}
          </view>
        </view>

        <view class="info-box">
          <view class="info-row">
            <text>手机号</text>
            <text>{{ item.phone || '-' }}</text>
          </view>

          <view class="info-row">
            <text>公司名称</text>
            <text>{{ item.company_name || '-' }}</text>
          </view>

          <view class="info-row">
            <text>注册时间</text>
            <text>{{ item.created_at || '-' }}</text>
          </view>

          <view v-if="item.reject_reason" class="info-row">
            <text>驳回原因</text>
            <text style="color:#f56c6c">{{ item.reject_reason }}</text>
          </view>
        </view>

        <view v-if="item.status==='pending'" class="action-row">
          <button class="reject-btn" @click="openRejectAccount(item)">
            驳回
          </button>

          <button class="approve-btn" @click="handleApproveAccount(item)">
            通过
          </button>
        </view>

        <view v-else-if="item.status==='approved' && item.role!=='platform_admin'" class="action-row">
          <button class="reject-btn" @click="handleDisableAccount(item)">
            清退该账号
          </button>
        </view>

        <view v-else-if="item.status==='disabled'" class="action-row">
          <button class="approve-btn" @click="handleEnableAccount(item)">
            恢复账号
          </button>
        </view>
      </view>
    </view>

    <!-- 以下区块保留代码，MVP 主流程暂不展示 -->
    <view v-if="false && activeTab === 'quota'">
      <view class="section-head">
        <view class="section-title">预付款额度审核</view>
        <view class="section-desc">回收商提前提交预付款凭证，审核后形成可用额度</view>
      </view>

      <view v-if="pendingRechargeList.length === 0" class="empty">
        暂无预付款凭证待审核
      </view>

      <view
        v-for="item in pendingRechargeList"
        :key="item.id"
        class="card"
      >
        <view class="card-head">
          <view>
            <view class="card-title">{{ item.companyName || '回收商公司' }}</view>
            <view class="card-sub">预付款凭证审核</view>
          </view>

          <view class="status-pill waiting">
            待审核
          </view>
        </view>

        <view class="amount-card">
          <view class="amount-label">申请增加额度</view>
          <view class="amount-money">¥{{ formatMoney(item.amount) }}</view>
        </view>

        <view class="info-box">
          <view class="info-row">
            <text>公司ID</text>
            <text>{{ item.companyId || '-' }}</text>
          </view>

          <view class="info-row">
            <text>提交人</text>
            <text>{{ item.applyUserName || '-' }}</text>
          </view>

          <view class="info-row">
            <text>提交时间</text>
            <text>{{ item.createTime || '-' }}</text>
          </view>

          <view class="info-row">
            <text>备注</text>
            <text>{{ item.remark || '-' }}</text>
          </view>
        </view>

        <image
          v-if="item.screenshot"
          class="proof-img"
          :src="item.screenshot"
          mode="aspectFill"
          @click="previewImage(item.screenshot)"
        />

        <view class="action-row">
          <button class="reject-btn" @click="openRejectRecharge(item)">
            驳回
          </button>

          <button class="approve-btn" @click="approveRecharge(item)">
            通过并增加额度
          </button>
        </view>
      </view>
    </view>

    <view v-if="false && activeTab === 'settlement'">
      <view class="section-head">
        <view class="section-title">线下结算确认</view>
        <view class="section-desc">回收商已确认收货后，由平台确认线下结算完成</view>
      </view>

      <view v-if="pendingSettlementList.length === 0" class="empty">
        暂无待确认结算订单
      </view>

      <view
        v-for="item in pendingSettlementList"
        :key="item.id"
        class="card"
      >
        <view class="card-head">
          <view>
            <view class="card-title">{{ getDeviceTitle(item) }}</view>
            <view class="card-sub">订单号：{{ item.no || item.id }}</view>
          </view>

          <view class="status-pill processing">
            待结算确认
          </view>
        </view>

        <view class="money-detail">
          <view class="money-title">平台金额明细</view>

          <view class="money-row">
            <text>回收商完整报价</text>
            <text>¥{{ formatMoney(getPlatformAmount(item).recyclerQuoteAmount) }}</text>
          </view>

          <view class="money-row">
            <text>平台收入</text>
            <text>¥{{ formatMoney(getPlatformAmount(item).platformFeeAmount) }}</text>
          </view>

          <view class="money-row">
            <text>商家可见金额</text>
            <text>¥{{ formatMoney(getPlatformAmount(item).merchantBaseAmount) }}</text>
          </view>

          <view class="money-row">
            <text>老板抽成</text>
            <text>¥{{ formatMoney(getPlatformAmount(item).merchantOwnerCommission) }}</text>
          </view>

          <view class="money-row">
            <text>员工抽成</text>
            <text>¥{{ formatMoney(getPlatformAmount(item).merchantStaffCommission) }}</text>
          </view>

          <view class="money-row total">
            <text>商家真实金额</text>
            <text>¥{{ formatMoney(getPlatformAmount(item).merchantRealAmount) }}</text>
          </view>
        </view>

        <view class="info-box">
          <view class="info-row">
            <text>商家公司</text>
            <text>{{ item.merchantCompanyName || item.company_name || '-' }}</text>
          </view>

          <view class="info-row">
            <text>成交回收商</text>
            <text>{{ item.selectedRecyclerCompanyName || '-' }}</text>
          </view>

          <view class="info-row">
            <text>报价员工</text>
            <text>{{ item.selectedQuoteUserName || '-' }}</text>
          </view>

          <view class="info-row">
            <text>商家发货时间</text>
            <text>{{ item.merchantShipTime || '-' }}</text>
          </view>

          <view class="info-row">
            <text>回收商收货时间</text>
            <text>{{ item.recyclerReceiveTime || '-' }}</text>
          </view>

          <view class="info-row">
            <text>快递单号</text>
            <text>{{ item.expressNo || '-' }}</text>
          </view>
        </view>

        <button class="approve-btn full" @click="confirmSettlement(item)">
          确认线下结算完成
        </button>
      </view>
    </view>

    <view v-if="false && activeTab === 'cancel'">
      <view class="section-head">
        <view class="section-title">取消订单审核</view>
        <view class="section-desc">商家或回收商提交取消申请后，由平台管理员审核</view>
      </view>

      <view v-if="pendingCancelList.length === 0" class="empty">
        暂无取消订单申请
      </view>

      <view
        v-for="item in pendingCancelList"
        :key="item.id"
        class="card"
      >
        <view class="card-head">
          <view>
            <view class="card-title">{{ getDeviceTitle(item) }}</view>
            <view class="card-sub">订单号：{{ item.no || item.id }}</view>
          </view>

          <view class="status-pill warning">
            取消审核中
          </view>
        </view>

        <view class="info-box">
          <view class="info-row">
            <text>申请人</text>
            <text>{{ item.cancelApplyUserName || '-' }}</text>
          </view>

          <view class="info-row">
            <text>申请角色</text>
            <text>{{ roleText(item.cancelApplyRole) }}</text>
          </view>

          <view class="info-row">
            <text>注册时间</text>
            <text>{{ item.cancelApplyTime || '-' }}</text>
          </view>

          <view class="info-row">
            <text>取消原因</text>
            <text>{{ item.cancelApplyReason || '-' }}</text>
          </view>
        </view>

        <view class="money-detail">
          <view class="money-title">订单金额</view>

          <view class="money-row">
            <text>回收商完整报价</text>
            <text>¥{{ formatMoney(getPlatformAmount(item).recyclerQuoteAmount) }}</text>
          </view>

          <view class="money-row">
            <text>商家可见金额</text>
            <text>¥{{ formatMoney(getPlatformAmount(item).merchantBaseAmount) }}</text>
          </view>
        </view>

        <view class="action-row">
          <button class="reject-btn" @click="openRejectCancel(item)">
            驳回取消
          </button>

          <button class="approve-btn" @click="approveCancel(item)">
            通过取消
          </button>
        </view>
      </view>
    </view>

    <view v-if="false && activeTab === 'staff'">
      <view class="section-head">
        <view class="section-title">员工信息</view>
        <view class="section-desc">平台管理员可查看全部商家和回收商员工信息</view>
      </view>

      <view v-if="staffList.length === 0" class="empty">
        暂无员工信息
      </view>

      <view
        v-for="item in staffList"
        :key="item.id"
        class="card"
      >
        <view class="card-head">
          <view>
            <view class="card-title">{{ item.username || '员工账号' }}</view>
            <view class="card-sub">{{ roleText(item.role) }}</view>
          </view>

          <view :class="['status-pill', item.status === 'approved' ? 'success' : 'waiting']">
            {{ accountStatusText(item.status) }}
          </view>
        </view>

        <view class="info-box">
          <view class="info-row">
            <text>手机号</text>
            <text>{{ item.phone || '-' }}</text>
          </view>

          <view class="info-row">
            <text>公司名称</text>
            <text>{{ item.company_name || '-' }}</text>
          </view>

          <view class="info-row">
            <text>公司ID</text>
            <text>{{ item.company_id || '-' }}</text>
          </view>

          <view class="info-row">
            <text>创建时间</text>
            <text>{{ item.created_at || '-' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 驳回弹窗 -->
    <view v-if="rejectPopupVisible" class="mask" @click="closeRejectPopup">
      <view class="popup" @click.stop>
        <view class="popup-title">{{ rejectTitle }}</view>

        <view class="form-item">
          <view class="label">驳回原因</view>
          <textarea
            class="textarea"
            v-model="rejectReason"
            placeholder="请输入驳回原因"
          />
        </view>

        <view class="popup-actions">
          <view class="popup-btn cancel" @click="closeRejectPopup">
            取消
          </view>

          <view class="popup-btn danger" @click="submitReject">
            确认驳回
          </view>
        </view>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  getPlatformOrderAmountView,
  formatMoney
} from '@/utils/moneyMock.js'
import { getDeviceTitle, getNowText } from '@/utils/tradeFlow.js'
import { releaseIfFrozen, recordRechargeFlow } from '@/utils/fundFlow.js'
import {
  getAccountState,
  approveAccount as mockApproveAccount,
  rejectAccount as mockRejectAccount
} from '@/utils/accountMock.js'
import {
  getPendingAccounts,
  getAllAccounts,
  approveAccount,
  rejectAccount,
  disableAccount,
  enableAccount
} from '@/api/account.js'
import {
  getRechargeApplies,
  approveRecharge as apiApproveRecharge,
  rejectRecharge as apiRejectRecharge,
  approveCancelOrder,
  rejectCancelOrder
} from '@/api/fund.js'
import { getAdminTrades } from '@/api/trade.js'

const FUND_KEY = 'recyclerFundPoolList'
const RECHARGE_KEY = 'recyclerRechargeApplyList'

const currentUser = ref({})
const accountState = ref(getAccountState())
const pendingAccountList = ref([])
const approvedAccountList = ref([])
const rejectedAccountList = ref([])
const approvedAccountCount = ref(0)
const rejectedAccountCount = ref(0)
const accountTab = ref('pending')
const accountSearch = ref('')

const currentAccountList = computed(() => {
  const list = accountTab.value === 'approved' ? approvedAccountList.value : accountTab.value === 'rejected' ? rejectedAccountList.value : pendingAccountList.value
  const term = accountSearch.value.trim().toLowerCase()
  return list.filter(item => !term || [item.id,item.company_id,item.company_name,item.nickname,item.username,item.phone].some(v => String(v || '').toLowerCase().includes(term)))
})
const inquiryList = ref([])
const fundList = ref([])
const rechargeApplyList = ref([])
const activeTab = ref('account')

const rejectPopupVisible = ref(false)
const rejectType = ref('')
const rejectTarget = ref({})
const rejectReason = ref('')

onShow(() => {
  currentUser.value = uni.getStorageSync('userInfo') ||
    uni.getStorageSync('currentUser') ||
    {}

  if (currentUser.value.role !== 'platform_admin') {
    uni.showToast({
      title: '暂无平台审核权限',
      icon: 'none'
    })

    uni.reLaunch({
      url: '/pages/home/home'
    })
    return
  }

  loadData()
})

const staffList = computed(() => {
  return (accountState.value.accounts || []).filter(item => {
    return item.role === 'merchant_staff' ||
      item.role === 'recycler_staff' ||
      item.role === 'recycler_keeper'
  })
})

const pendingRechargeList = computed(() => {
  return rechargeApplyList.value.filter(item => item.status === 'pending')
})

const pendingSettlementList = computed(() => {
  return inquiryList.value.filter(item => item.tradeStatus === 'recycler_received')
})

const pendingCancelList = computed(() => {
  return inquiryList.value.filter(item => item.cancelApplyStatus === 'pending')
})

const tabs = computed(() => {
  return [
    {
      key: 'account',
      name: '账号',
      badge: pendingAccountList.value.length
    },
    {
      key: 'quota',
      name: '预付款',
      badge: pendingRechargeList.value.length
    },
    {
      key: 'settlement',
      name: '结算',
      badge: pendingSettlementList.value.length
    },
    {
      key: 'cancel',
      name: '取消',
      badge: pendingCancelList.value.length
    },
    {
      key: 'staff',
      name: '员工',
      badge: staffList.value.length
    }
  ]
})

const rejectTitle = computed(() => {
  const map = {
    account: '驳回账号申请',
    recharge: '驳回预付款凭证',
    cancel: '驳回取消订单申请'
  }

  return map[rejectType.value] || '驳回'
})

async function loadAccountData() {
  try {
    const [pendingRes, approvedRes, rejectedRes, disabledRes] = await Promise.all([
      getAllAccounts('pending'),
      getAllAccounts('approved'),
      getAllAccounts('rejected'),
      getAllAccounts('disabled')
    ])
    pendingAccountList.value = pendingRes.list || pendingRes || []
    approvedAccountList.value = approvedRes.list || approvedRes || []
    const rejectedArr = rejectedRes.list || rejectedRes || []
    const disabledArr = disabledRes.list || disabledRes || []
    rejectedAccountList.value = [...disabledArr, ...rejectedArr]
    approvedAccountCount.value = approvedAccountList.value.length
    rejectedAccountCount.value = rejectedAccountList.value.length
  } catch (error) {
    accountState.value = getAccountState()
    const all = accountState.value.accounts || []
    pendingAccountList.value = all.filter(item => item.status === 'pending')
    approvedAccountList.value = all.filter(item => item.status === 'approved')
    rejectedAccountList.value = all.filter(item => item.status === 'rejected')
    approvedAccountCount.value = approvedAccountList.value.length
    rejectedAccountCount.value = rejectedAccountList.value.length
  }
}

function switchAccountTab(tab) {
  accountTab.value = tab
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.reLaunch({ url: '/pages/home/home' })
  }
}

function loadData() {
  loadAccountData()
  loadRechargeData()
  loadTradeData()
}

async function loadRechargeData() {
  try {
    const res = await getRechargeApplies()
    rechargeApplyList.value = (res.list || []).map(item => ({
      id: item.id,
      companyId: Number(item.company_id),
      companyName: item.company_name || '',
      applyUserId: item.apply_user_id,
      applyUserName: item.apply_user_name || '',
      amount: Number(item.amount || 0),
      screenshot: item.proof_image || '',
      status: item.status,
      createTime: item.create_time || '',
      payoutTime: item.review_time || '',
      rejectReason: item.reject_reason || ''
    }))
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  fundList.value = uni.getStorageSync(FUND_KEY) || []
  rechargeApplyList.value = uni.getStorageSync(RECHARGE_KEY) || []
}

async function loadTradeData() {
  try {
    const res = await getAdminTrades()
    inquiryList.value = (res.list || []).map(item => ({
      ...item,
      quotes: Array.isArray(item.quotes) ? item.quotes : [],
      cancelApplyStatus: item.cancelApplyStatus || item.order?.cancelApplyStatus || '',
      cancelApplyReason: item.cancelApplyReason || item.order?.cancelApplyReason || '',
      orderId: item.orderId || item.order?.id || null
    }))
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  const list = uni.getStorageSync('inquiryList') || []
  inquiryList.value = list.map(item => ({
    ...item,
    quotes: Array.isArray(item.quotes) ? item.quotes : []
  }))
}

function saveInquiryList() {
  uni.setStorageSync('inquiryList', inquiryList.value)
}

function saveFundList() {
  uni.setStorageSync(FUND_KEY, fundList.value)
}

function saveRechargeList() {
  uni.setStorageSync(RECHARGE_KEY, rechargeApplyList.value)
}

function handleApproveAccount(item) {
  uni.showModal({
    title: '确认通过',
    content: `确认通过 ${item.nickname || item.username || '该账号'} 的账号申请吗？`,
    confirmText: '通过',
    confirmColor: '#4b5563',
    success: async res => {
      if (!res.confirm) return

      try {
        await approveAccount(item.id)
        await loadAccountData()

        uni.showToast({
          title: '已通过',
          icon: 'success'
        })
      } catch (error) {
        const result = mockApproveAccount(item.id)

        if (!result.ok) {
          return
        }

        await loadAccountData()

        uni.showToast({
          title: '已通过',
          icon: 'success'
        })
      }
    }
  })
}

function handleDisableAccount(item) {
  uni.showModal({
    title: '确认清退',
    content: `确认清退「${item.nickname || item.username || '该账号'}」吗？清退后该账号将无法登录。`,
    confirmText: '清退',
    confirmColor: '#f56c6c',
    success: async res => {
      if (!res.confirm) return
      try {
        await disableAccount(item.id)
        await loadAccountData()
        uni.showToast({ title: '已清退', icon: 'success' })
      } catch (error) {
        // 失败提示已由 request.js 弹出
      }
    }
  })
}

function handleEnableAccount(item) {
  uni.showModal({
    title: '恢复账号',
    content: `确认恢复「${item.nickname || item.username || '该账号'}」吗？恢复后可重新登录。`,
    confirmText: '恢复',
    confirmColor: '#4b5563',
    success: async res => {
      if (!res.confirm) return
      try {
        await enableAccount(item.id)
        await loadAccountData()
        uni.showToast({ title: '已恢复', icon: 'success' })
      } catch (error) {
        // 失败提示已由 request.js 弹出
      }
    }
  })
}

function openRejectAccount(item) {
  rejectType.value = 'account'
  rejectTarget.value = item
  rejectReason.value = ''
  rejectPopupVisible.value = true
}

function approveRecharge(item) {
  uni.showModal({
    title: '确认增加额度',
    content: `确认通过 ${item.companyName || '该回收商'} 的预付款凭证，并增加可用额度 ¥${formatMoney(item.amount)}？`,
    confirmText: '通过',
    confirmColor: '#4b5563',
    success: async res => {
      if (!res.confirm) return

      try {
        await apiApproveRecharge(item.id)
        await loadRechargeData()
        uni.showToast({ title: '额度已增加', icon: 'success' })
        return
      } catch (error) {
        return // 请求失败不得恢复历史模拟数据
      }

      const apply = rechargeApplyList.value.find(row => Number(row.id) === Number(item.id))

      if (!apply) return

      apply.status = 'approved'
      apply.payoutTime = getNowText()
      apply.rejectReason = ''

      const companyId = Number(apply.companyId)

      let fund = fundList.value.find(row => Number(row.companyId) === companyId)

      if (!fund) {
        fund = {
          companyId,
          companyName: apply.companyName || `中晨回收${companyId}`,
          balance: 0,
          frozenAmount: 0,
          updatedTime: ''
        }

        fundList.value.unshift(fund)
      }

      fund.balance = Number(fund.balance || 0) + Number(apply.amount || 0)
      fund.updatedTime = getNowText()

      saveRechargeList()
      saveFundList()

      // 充值流水补登:写入一条 recharge 流水(余额已在上方累加,这里只记账)
      recordRechargeFlow(companyId, apply.amount, {
        operator: '平台管理员',
        remark: `${apply.companyName || '回收商'} 充值审核通过`
      })

      loadData()

      uni.showToast({
        title: '额度已增加',
        icon: 'success'
      })
    }
  })
}

function openRejectRecharge(item) {
  rejectType.value = 'recharge'
  rejectTarget.value = item
  rejectReason.value = ''
  rejectPopupVisible.value = true
}

function confirmSettlement(item) {
  const amountView = getPlatformAmount(item)

  uni.showModal({
    title: '确认线下结算完成',
    content: `确认该订单已完成线下结算？商家真实金额 ¥${formatMoney(amountView.merchantRealAmount)}。`,
    confirmText: '确认完成',
    cancelText: '取消',
    confirmColor: '#4b5563',
    success: res => {
      if (!res.confirm) return

      const target = inquiryList.value.find(row => Number(row.id) === Number(item.id))

      if (!target) return

      target.tradeStatus = 'platform_paid'
      target.status = '交易完成'
      target.quoteStatus = 'done'
      target.platformSettleTime = getNowText()
      target.platformPayTime = getNowText()
      target.quotaStatus = 'finished'
      target.quotaFinishTime = getNowText()

      saveInquiryList()
      loadData()

      uni.showToast({
        title: '结算已确认',
        icon: 'success'
      })
    }
  })
}

function approveCancel(item) {
  uni.showModal({
    title: '确认取消订单',
    content: '取消通过后，该订单将结束。如已占用额度，后续应释放额度记录。',
    confirmText: '通过取消',
    cancelText: '再看看',
    confirmColor: '#ff5a3c',
    success: async res => {
      if (!res.confirm) return

      const orderId = item.orderId || item.order?.id

      if (orderId) {
        try {
          await approveCancelOrder(orderId)
          await loadTradeData()
          uni.showToast({ title: '已取消订单', icon: 'success' })
          return
        } catch (error) {
          return // 请求失败不得恢复历史模拟数据
        }
      }

      const target = inquiryList.value.find(row => Number(row.id) === Number(item.id))

      if (!target) return

      target.cancelApplyStatus = 'approved'
      target.cancelpayoutTime = getNowText()
      target.cancelRejectReason = ''
      target.status = '订单已取消'
      target.quoteStatus = 'cancelled'
      target.tradeStatus = 'cancelled'
      target.quotaStatus = 'released'
      target.quotaReleaseTime = getNowText()

      // P7 资金联动:订单取消 → 若仍处于冻结(未扣款)状态,统一释放冻结额度
      releaseIfFrozen(target, {
        orderNo: target.orderNo,
        operator: '平台管理员',
        remark: '取消订单审核通过,释放冻结额度'
      })

      saveInquiryList()
      loadData()

      uni.showToast({
        title: '已取消订单',
        icon: 'success'
      })
    }
  })
}

function openRejectCancel(item) {
  rejectType.value = 'cancel'
  rejectTarget.value = item
  rejectReason.value = ''
  rejectPopupVisible.value = true
}

function submitReject() {
  if (!rejectReason.value.trim()) {
    uni.showToast({
      title: '请输入驳回原因',
      icon: 'none'
    })
    return
  }

  if (rejectType.value === 'account') {
    handleRejectAccount()
    return
  }

  if (rejectType.value === 'recharge') {
    rejectRecharge()
    return
  }

  if (rejectType.value === 'cancel') {
    rejectCancel()
  }
}

async function handleRejectAccount() {
  const accountId = rejectTarget.value.id
  const reason = rejectReason.value.trim()

  try {
    await rejectAccount(accountId, reason)
    closeRejectPopup()
    await loadAccountData()

    uni.showToast({
      title: '已驳回',
      icon: 'success'
    })
  } catch (error) {
    const result = mockRejectAccount(accountId, reason)

    if (!result.ok) {
      return
    }

    closeRejectPopup()
    await loadAccountData()

    uni.showToast({
      title: '已驳回',
      icon: 'success'
    })
  }
}

async function rejectRecharge() {
  try {
    await apiRejectRecharge(rejectTarget.value.id, rejectReason.value)
    closeRejectPopup()
    await loadRechargeData()
    uni.showToast({ title: '已驳回', icon: 'success' })
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  const target = rechargeApplyList.value.find(row => Number(row.id) === Number(rejectTarget.value.id))

  if (!target) return

  target.status = 'rejected'
  target.payoutTime = getNowText()
  target.rejectReason = rejectReason.value

  saveRechargeList()
  closeRejectPopup()
  loadData()

  uni.showToast({
    title: '已驳回',
    icon: 'success'
  })
}

async function rejectCancel() {
  const orderId = rejectTarget.value.orderId || rejectTarget.value.order?.id

  if (orderId) {
    try {
      await rejectCancelOrder(orderId, rejectReason.value)
      closeRejectPopup()
      await loadTradeData()
      uni.showToast({ title: '已驳回', icon: 'success' })
      return
    } catch (error) {
      return // 请求失败不得恢复历史模拟数据
    }
  }

  const target = inquiryList.value.find(row => Number(row.id) === Number(rejectTarget.value.id))

  if (!target) return

  target.cancelApplyStatus = 'rejected'
  target.cancelpayoutTime = getNowText()
  target.cancelRejectReason = rejectReason.value

  saveInquiryList()
  closeRejectPopup()
  loadData()

  uni.showToast({
    title: '已驳回',
    icon: 'success'
  })
}

function closeRejectPopup() {
  rejectPopupVisible.value = false
  rejectType.value = ''
  rejectTarget.value = {}
  rejectReason.value = ''
}

function getPlatformAmount(item) {
  const view = getPlatformOrderAmountView(item)

  return {
    recyclerQuoteAmount:
      view.recyclerQuoteAmount ||
      item.selectedRecyclerQuoteAmount ||
      item.selectedAmount ||
      0,

    platformFeeRate:
      view.platformFeeRate ||
      item.selectedPlatformFeeRate ||
      0.02,

    platformFeeAmount:
      view.platformFeeAmount ||
      item.selectedPlatformFeeAmount ||
      0,

    merchantBaseAmount:
      view.merchantBaseAmount ||
      item.selectedMerchantBaseAmount ||
      item.selectedMerchantAmount ||
      0,

    merchantOwnerRate:
      view.merchantOwnerRate ||
      item.selectedMerchantOwnerRate ||
      0,

    merchantOwnerCommission:
      view.merchantOwnerCommission ||
      item.selectedMerchantOwnerCommission ||
      0,

    merchantStaffRate:
      view.merchantStaffRate ||
      item.selectedMerchantStaffRate ||
      0,

    merchantStaffCommission:
      view.merchantStaffCommission ||
      item.selectedMerchantStaffCommission ||
      0,

    merchantRealAmount:
      view.merchantRealAmount ||
      item.selectedMerchantRealAmount ||
      item.selectedMerchantAmount ||
      0,

    merchantDisplayAmount:
      view.merchantDisplayAmount ||
      item.selectedMerchantDisplayAmount ||
      Math.floor(Number(item.selectedMerchantAmount || 0))
  }
}

function roleText(role) {
  const map = {
    platform_admin: '平台管理员',
    merchant_owner: '商家老板',
    merchant_staff: '商家员工',
    recycler_owner: '回收商老板',
    recycler_keeper: '回收商库管',
    recycler_staff: '回收商员工'
  }

  return map[role] || role || '-'
}

function accountStatusText(status) {
  const map = {
    pending: '待平台审核',
    approved: '已通过',
    rejected: '已驳回'
  }

  return map[status] || '-'
}

function previewImage(url) {
  uni.previewImage({
    urls: [url],
    current: url
  })
}
</script>




<style scoped>

.page {
  min-height: 100vh;
  background: #f3f5f7;
  box-sizing: border-box;
}

.hero {
  margin: 24rpx;
  padding: 34rpx;
  padding-top: calc(var(--status-bar-height) + 60rpx);
  border-radius: 16rpx;
  background: #17324d;
  color: #ffffff;
  box-shadow: none;
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.hello {
  font-size: 28rpx;
  opacity: 0.9;
}

.title {
  margin-top: 10rpx;
  font-size: 46rpx;
  font-weight: 600;
}

.desc {
  margin-top: 12rpx;
  font-size: 25rpx;
  line-height: 38rpx;
  opacity: 0.92;
}

.hero-icon {
  width: 84rpx;
  height: 84rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  font-weight: 600;
}

.stats {
  display: flex;
  margin-top: 34rpx;
  gap: 16rpx;
}

.stat-item {
  flex: 1;
  padding: 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.22);
  text-align: center;
}

.stat-number {
  font-size: 40rpx;
  font-weight: 600;
}

.stat-label {
  margin-top: 6rpx;
  font-size: 24rpx;
}

.tabs {
  display: flex;
  margin: 0 24rpx 24rpx;
  padding: 8rpx;
  border-radius: 999rpx;
  background: #ffffff;
  box-shadow: none;
  overflow-x: auto;
}

.tab {
  position: relative;
  flex: 0 0 20%;
  height: 72rpx;
  line-height: 72rpx;
  text-align: center;
  border-radius: 999rpx;
  color: #64748b;
  font-size: 25rpx;
  font-weight: bold;
}

.tab.active {
  background: #17324d;
  color: #ffffff;
}

.tab-badge {
  position: absolute;
  right: 4rpx;
  top: -8rpx;
  min-width: 30rpx;
  height: 30rpx;
  line-height: 30rpx;
  border-radius: 999rpx;
  background: #ff5a3c;
  color: #ffffff;
  font-size: 24rpx;
}

.section-head {
  margin: 0 24rpx 24rpx;
}

.section-title {
  color: #222222;
  font-size: 34rpx;
  font-weight: 600;
}

.section-desc {
  margin-top: 8rpx;
  color: #888888;
  font-size: 24rpx;
  line-height: 36rpx;
}

.empty {
  margin: 40rpx 24rpx;
  padding: 70rpx 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  color: #999999;
  text-align: center;
  font-size: 28rpx;
}

.card {
  margin: 0 24rpx 24rpx;
  padding: 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.card-title {
  color: #111111;
  font-size: 32rpx;
  font-weight: 600;
}

.card-sub {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.status-pill {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
  font-weight: bold;
}

.status-pill.waiting {
  background: #fff7e6;
  color: #d97706;
}

.status-pill.processing {
  background: #eef0f4;
  color: #374151;
}

.status-pill.warning {
  background: #fff7e6;
  color: #d97706;
}

.status-pill.success {
  background: #ecfdf3;
  color: #18a058;
}

.info-box,
.money-detail {
  margin-top: 24rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: #f6f7f9;
}

.info-row,
.money-row {
  display: flex;
  justify-content: space-between;
  color: #666666;
  font-size: 24rpx;
  line-height: 42rpx;
  gap: 20rpx;
}

.info-row text:last-child,
.money-row text:last-child {
  text-align: right;
  color: #333333;
}

.amount-card {
  margin-top: 24rpx;
  padding: 24rpx;
  border-radius: 16rpx;
  background: #f6f7f9;
}

.amount-label {
  color: #888888;
  font-size: 24rpx;
}

.amount-money {
  margin-top: 8rpx;
  color: #ff5a3c;
  font-size: 46rpx;
  font-weight: 600;
}

.proof-img {
  width: 190rpx;
  height: 190rpx;
  margin-top: 22rpx;
  border-radius: 20rpx;
  background: #eeeeee;
}

.money-title {
  color: #222222;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 12rpx;
}

.money-row.total {
  margin-top: 10rpx;
  padding-top: 12rpx;
  border-top: 1rpx solid #e5edf5;
  color: #ff5a3c;
  font-weight: bold;
}

.action-row {
  display: flex;
  gap: 18rpx;
  margin-top: 26rpx;
}

.reject-btn,
.approve-btn {
  flex: 1;
  height: 78rpx;
  line-height: 78rpx;
  border-radius: 999rpx;
  font-size: 27rpx;
  font-weight: bold;
}

.reject-btn {
  background: #fff0eb;
  color: #ff5a3c;
}

.approve-btn {
  background: #17324d;
  color: #ffffff;
}

.approve-btn.full {
  margin-top: 26rpx;
  width: 100%;
}

.reject-btn::after,
.approve-btn::after {
  border: none;
}

.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  box-sizing: border-box;
}

.popup {
  width: 100%;
  padding: 36rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-sizing: border-box;
}

.popup-title {
  text-align: center;
  color: #111111;
  font-size: 36rpx;
  font-weight: 600;
}

.form-item {
  margin-top: 28rpx;
}

.label {
  margin-bottom: 14rpx;
  color: #333333;
  font-size: 26rpx;
  font-weight: bold;
}

.textarea {
  width: 100%;
  min-height: 150rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f5f8fb;
  font-size: 28rpx;
  box-sizing: border-box;
}

.popup-actions {
  display: flex;
  gap: 18rpx;
  margin-top: 32rpx;
}

.popup-btn {
  flex: 1;
  height: 82rpx;
  line-height: 82rpx;
  text-align: center;
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: bold;
}

.popup-btn.cancel {
  background: #f1f2f4;
  color: #555555;
}

.popup-btn.danger {
  background: #ff5a3c;
  color: #ffffff;
}

.safe-bottom {
  height: 50rpx;
}
.status-tabs {
  display: flex;
  margin: 20rpx 30rpx 0;
  background: #f0f4f8;
  border-radius: 16rpx;
  padding: 6rpx;
}
.status-tab {
  flex: 1;
  text-align: center;
  padding: 14rpx 0;
  border-radius: 12rpx;
  font-size: 26rpx;
  color: #888;
}
.status-tab.active {
  background: #fff;
  color: #17324d;
  font-weight: bold;
}
.badge {
  display: inline-block;
  background: #ff4d4f;
  color: #fff;
  border-radius: 20rpx;
  padding: 0 10rpx;
  font-size: 24rpx;
  margin-left: 4rpx;
}
.badge-gray {
  display: inline-block;
  background: #ccc;
  color: #fff;
  border-radius: 20rpx;
  padding: 0 10rpx;
  font-size: 24rpx;
  margin-left: 4rpx;
}
.status-pill.approved { background: #e6f7ee; color: #52c41a; }
.status-pill.rejected { background: #fff1f0; color: #f56c6c; }
.back-btn {
  color: #fff;
  font-size: 70rpx;
  line-height: 60rpx;
  padding: 0 24rpx 0 10rpx;
  opacity: 0.9;
  font-weight: 300;
  cursor: pointer;
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
