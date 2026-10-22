<template>
  <view class="page">
    <!-- 白色状态栏占位 -->
    <view class="status-bar-placeholder"></view>

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ currentUser.username || '未登录' }}</view>
          <view class="title" v-if="currentUser.role !== 'platform_admin'">{{ roleText(currentUser.role) }}</view>
          <view class="title" v-else>中晨回收平台</view>
        </view>
      </view>

      <view class="search-card" @click="goOrderSearch">
        <image class="search-icon" src="/static/business/search.svg" mode="aspectFit" />
        <view class="search-text">按订单号查询订单</view>
        <text class="search-arrow">›</text>
      </view>

      <view class="stats-row">
        <view class="stat-item">
          <view class="stat-number">{{ todayStats.todo }}</view>
          <view class="stat-label">{{ todayStats.todoLabel }}</view>
        </view>

        <view class="stat-line"></view>

        <view class="stat-item">
          <view class="stat-number">{{ todayStats.done }}</view>
          <view class="stat-label">{{ todayStats.doneLabel }}</view>
        </view>

        <view class="stat-line"></view>

        <view class="stat-item">
          <view class="stat-number">{{ currentUser.company_id || '-' }}</view>
          <view class="stat-label">公司ID</view>
        </view>
      </view>
    </view>

    <view class="content">
      <view v-if="currentUser.role==='platform_admin' && (depositAlerts.pending || depositAlerts.overdue)" class="section" @click="openDepositManagement">
        <view class="section-title">保证金待办</view>
        <view>待核实申请 {{ depositAlerts.pending }} 家 · 注册满一个月未缴纳 {{ depositAlerts.overdue }} 家</view>
        <view>进入资金池管理 → 商家，查看注册时间并登记跟进。</view>
      </view>

      <!-- 工作台 -->
      <view v-if="activeTab === 'workbench'">
        <view class="filter-row">
          <view class="filter-pill">
            {{ currentUser.company_name || '当前公司' }}
            
          </view>

          <view class="filter-pill">
            {{ roleText(currentUser.role) }}
            
          </view>
        </view>

        <view v-if="false && isRecyclerRole(currentUser.role)" class="fund-mini-card">
          <view>
            <view class="fund-mini-label">资金池余额</view>
            <view class="fund-mini-money">¥{{ formatMoney(companyFund.balance) }}</view>
          </view>

          <view :class="['fund-mini-status', canQuoteByFund ? 'safe' : 'danger']">
            {{ canQuoteByFund ? '可报价' : '不可报价' }}
          </view>
        </view>

        <view class="section-row">
          <view class="section-title">业务入口</view>
          <view class="section-more">常用功能</view>
        </view>

        <view class="menu-grid">
          <view
            v-for="item in menuList"
            :key="item.title"
            :class="['menu-item', item.disabled ? 'disabled' : '']"
            @click="handleMenu(item)"
          >
            <view :class="['menu-icon-wrap', item.colorClass]">
              <image class="menu-icon" :src="businessIcon(item.title)" mode="aspectFit" />
              
            </view>
            <view class="menu-label">{{ item.title }}<text v-if="item.badge" class="entry-count">{{ item.badge > 99 ? '99+' : item.badge }}</text></view>
          </view>
        </view>
      </view>

      <!-- 统计 -->
      <view v-if="activeTab === 'stats'" class="tab-pane">
        <view class="section-row">
          <view class="section-title">数据概览</view>
          <view class="section-more">真实本地数据</view>
        </view>

        <view class="data-grid">
          <view
            v-for="item in dataCards"
            :key="item.label"
            class="data-card"
          >
            <view class="data-number">{{ item.value }}</view>
            <view class="data-label">{{ item.label }}</view>
          </view>
        </view>

        <view class="tips-card">
          <view class="tips-title">业务规则</view>
          <view class="tips-line">1. 商家发布设备后，回收商员工可在收到的询价中报价。</view>
          <view class="tips-line">2. 回收商之间不可查看彼此报价，只能看自己的报价。</view>
          <view class="tips-line">3. 商家确认报价后生成订单号，进入发货与验机流程。</view>
          <view class="tips-line">4. 验机完成后商家可确认完成或发起申诉，平台可关闭异常订单。</view>
        </view>
      </view>

      <!-- 订单 -->
      <view v-if="activeTab === 'orders'" class="tab-pane">
        <view class="section-row">
          <view class="section-title">{{ currentUser.role === 'platform_admin' ? '交易订单' : '订单提醒' }}</view>
          <view class="section-more">{{ currentUser.role === 'platform_admin' ? '来自平台交易流接口' : '真实数据' }}</view>
        </view>

        <view v-if="homeOrderCards.length === 0" class="empty-card">
          暂无订单或询价提醒
        </view>

        <view
          v-for="item in homeOrderCards"
          :key="item.id"
          class="order-card"
        >
          <view class="order-head">
            <view>
              <view class="order-shop">{{ item.shop }}</view>
              <view class="order-time">{{ item.time }}</view>
            </view>

            <view :class="['order-status', item.statusClass]">
              {{ item.statusText }}
            </view>
          </view>

          <view class="order-body">
            <view class="device-thumb">{{ item.icon }}</view>

            <view class="device-info">
              <view class="device-name">{{ item.device }}</view>
              <view class="device-desc">{{ item.desc }}</view>
            </view>

            <view class="order-action" @click="go(item.url)">
              处理
            </view>
          </view>
        </view>

        <view v-if="homeOrderCards.length > 0" class="end-text">
          已显示全部提醒
        </view>
      </view>

      <!-- 我的 -->
      <view v-if="activeTab === 'mine'">
        <view class="profile-card">
          <view class="profile-avatar">
            {{ avatarText }}
          </view>

          <view class="profile-main">
            <view class="profile-name">{{ currentUser.username || '未登录' }}</view>
            <view class="profile-role">{{ roleText(currentUser.role) }}</view>
          </view>
        </view>

        <view class="info-card">
          <view class="info-row">
            <text>手机号</text>
            <text>{{ currentUser.phone || '-' }}</text>
          </view>

          <view class="info-row">
            <text>公司名称</text>
            <text>{{ currentUser.company_name || '-' }}</text>
          </view>

          <view class="info-row">
            <text>公司类型</text>
            <text>{{ companyTypeText(currentUser.company_type) }}</text>
          </view>

          <view class="info-row">
            <text>当前权限</text>
            <text>{{ permissionSummary }}</text>
          </view>

          <view class="info-row">
            <text>账号状态</text>
            <text>{{ accountStatusText(currentUser.status) }}</text>
          </view>

          <view v-if="false && isRecyclerRole(currentUser.role)" class="info-row">
            <text>资金池余额</text>
            <text>¥{{ formatMoney(companyFund.balance) }}</text>
          </view>
        </view>

        <view class="account-actions">
          <view class="account-row" @click="openPasswordPopup">
            <view>
              <view class="account-title">修改密码</view>
              <view class="account-desc">验证原密码后设置新登录密码</view>
            </view>
            <view class="account-arrow">›</view>
          </view>

          <view class="account-row" @click="openCustomerService">
            <view>
              <view class="account-title">联系客服</view>
              <view class="account-desc">遇到问题可联系平台管理员</view>
            </view>
            <view class="account-arrow">›</view>
          </view>
        </view>

        <button class="logout-btn" @click="logout">
          退出登录
        </button>
      </view>
    </view>

    <!-- 修改密码弹窗 -->
    <view v-if="passwordPopupVisible" class="mask" @click="closePasswordPopup">
      <view class="popup" @click.stop>
        <view class="popup-title">修改密码</view>
        <view class="popup-desc">为账号 {{ currentUser.phone || '' }} 设置新登录密码</view>

        <view class="pwd-item">
          <view class="pwd-label">原密码</view>
          <input class="pwd-input" password v-model="passwordForm.oldPassword" placeholder="请输入当前密码" />
        </view>
        <view class="pwd-item">
          <view class="pwd-label">新密码</view>
          <input class="pwd-input" password v-model="passwordForm.newPassword" placeholder="至少3位" />
        </view>
        <view class="pwd-item">
          <view class="pwd-label">确认新密码</view>
          <input class="pwd-input" password v-model="passwordForm.confirmPassword" placeholder="请再次输入新密码" />
        </view>

        <view class="popup-actions">
          <view class="popup-btn cancel" @click="closePasswordPopup">取消</view>
          <view class="popup-btn confirm" @click="submitPassword">确认修改</view>
        </view>
      </view>
    </view>

    <!-- 自定义底部导航 -->
    <view class="bottom-nav">
      <view
        v-for="tab in bottomTabs"
        :key="tab.key"
        :class="['nav-item', activeTab === tab.key ? 'active' : '']"
        @click="handleBottomTab(tab)"
      >
        <image class="nav-icon" :src="activeTab === tab.key ? tab.activeIcon : tab.icon" mode="aspectFit" />
        <view class="nav-text">{{ tab.name }}</view>

        <view v-if="tab.badge" class="nav-badge">
          {{ tab.badge }}
        </view>
      </view>
    </view>

    <view class="float-btn" @click="refreshPage">
      ↻
    </view>
  </view>
</template>

<script setup>
import { get } from '@/utils/request.js'
import { clearAccountSession } from '@/utils/session.js'
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getAccountState } from '@/utils/accountMock.js'
import { formatMoney } from '@/utils/moneyMock.js'
import { canAccessPage } from '@/utils/permission.js'
import { getPendingAccounts, changePassword as changePasswordApi } from '@/api/account.js'
import {
  getAdminTrades,
  getMyOrders,
  getMyInquiries,
  getQuotesByInquiry,
  getRecyclerInquiries,
  getMyQuotes
} from '@/api/trade.js'
import {
  getAdminTradeStatus,
  getAdminTradeStatusLabel,
  getTradeFlowStatusLabel,
  resolveItemTradeStatus,
  getTradeFlowStatusClassName,
  normalizeAdminTradeList,
  ordersToAdminTradeFallback,
  getDeviceTitle,
  getNowText
} from '@/utils/tradeFlow.js'

const FUND_KEY = 'recyclerFundPoolList'
const RECHARGE_KEY = 'recyclerRechargeApplyList'

// 底部导航图标:用内联 SVG 线性图标，跨端稳定渲染，避免特殊字形乱码
const NAV_COLOR = {
  normal: '#9aa3b2',
  active: '#4b5563'
}

const NAV_ICON_PATHS = {
  workbench: "%3Cpath%20d='M3%2011l9-7%209%207'/%3E%3Cpath%20d='M5%2010v10h14V10'/%3E%3Cpath%20d='M9%2020v-6h6v6'/%3E",
  stats: "%3Cline%20x1='6'%20y1='20'%20x2='6'%20y2='12'/%3E%3Cline%20x1='12'%20y1='20'%20x2='12'%20y2='4'/%3E%3Cline%20x1='18'%20y1='20'%20x2='18'%20y2='14'/%3E",
  orders: "%3Crect%20x='5'%20y='3'%20width='14'%20height='18'%20rx='2'/%3E%3Cline%20x1='9'%20y1='8'%20x2='15'%20y2='8'/%3E%3Cline%20x1='9'%20y1='12'%20x2='15'%20y2='12'/%3E%3Cline%20x1='9'%20y1='16'%20x2='13'%20y2='16'/%3E",
  mine: "%3Ccircle%20cx='12'%20cy='8'%20r='4'/%3E%3Cpath%20d='M4%2020c0-4.2%204-6%208-6s8%201.8%208%206'/%3E"
}

function buildNavIcon(key, color) {
  const c = color.replace('#', '%23')
  return `data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%20fill='none'%20stroke='${c}'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'%3E${NAV_ICON_PATHS[key] || ''}%3C/svg%3E`
}

const currentUser = ref({})
const accountState = ref(getAccountState())
const inquiryList = ref([])
const fundList = ref([])
const rechargeApplyList = ref([])
function goOrderSearch() {
  const role = currentUser.value.role
  go(role === 'platform_admin' ? '/pages/platform/orders/orders' : isRecyclerRole(role) ? '/pages/recycler/order/order' : '/pages/merchant/order/order')
}
function businessIcon(title) {
  const rules = [['钱包|资金|付款|分成','credit-card'],['员工|审核','users'],['公司','briefcase'],['分析|数据','bar-chart-2'],['客服','headphones'],['抢单','zap'],['报价|询价|查询','search'],['订单','package']]
  return '/static/business/' + (rules.find(([pattern]) => new RegExp(pattern).test(title))?.[1] || 'file-text') + '.svg'
}
const activeTab = ref('workbench')
const platformTradeList = ref([])
const platformAccountPending = ref(0)

const passwordPopupVisible = ref(false)
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const depositAlerts=ref({pending:0,overdue:0})
function openDepositManagement(){uni.navigateTo({url:'/pages/platform/fund/fund'})}
onShow(async () => {
  // 隐藏原生 tabBar，仅保留页面内自定义底部导航，避免两条底栏重叠
  uni.hideTabBar({ animation: false, fail: () => {} })

  refreshCurrentUser()

  if (!currentUser.value.role) {
    uni.reLaunch({
      url: '/pages/login/login'
    })
    return
  }

  if(currentUser.value.role==='platform_admin'){
    try{const res=await get('/api/admin/merchant/deposits');depositAlerts.value={pending:(res.list||[]).filter(c=>c.pending_application).length,overdue:(res.list||[]).filter(c=>c.deposit_overdue).length}}catch(e){depositAlerts.value={pending:0,overdue:0}}
  }
  await loadHomeData()
})

async function loadHomeData() {
  const role = currentUser.value.role

  if (role === 'platform_admin') {
    await loadPlatformData()
    return
  }

  if (isMerchantRole(role)) {
    await loadMerchantHomeData()
    return
  }

  if (isRecyclerRole(role)) {
    await loadRecyclerHomeData()
  }
}

// 商家首页统计：从后端拉询价 + 报价 + 订单，替代本地 mock
async function loadMerchantHomeData() {
  inquiryList.value = []
  try {
    const [inqRes, orderRes] = await Promise.all([
      getMyInquiries(),
      getMyOrders().catch(() => ({ list: [] }))
    ])

    const orderByInquiry = {}
    ;(orderRes.list || []).forEach(order => {
      orderByInquiry[order.inquiry_id] = order
    })

    const list = inqRes.list || []

    await Promise.all(list.map(async item => {
      item.quotes = (item.quotes || []).map(q => ({ ...q, recyclerCompanyId: q.recyclerCompanyId || q.recycler_company_id, amount: q.price }))

      const order = orderByInquiry[item.id]
      if (order) {
        item.orderId = order.id
        item.tradeStatus = order.status
        item.status = order.status
        item.quoteStatus = 'accepted'
      }
    }))

    // getMyInquiries 已按公司过滤，直接标记公司归属，绕过 merchantInquiryList 的本地过滤
    inquiryList.value = list.map(item => ({
      ...item,
      merchantCompanyId: currentUser.value.company_id,
      merchantUserId: item.merchant_id
    }))
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  const local = uni.getStorageSync('inquiryList') || []
  inquiryList.value = local.map(item => ({
    ...item,
    quotes: Array.isArray(item.quotes) ? item.quotes : []
  }))
}

// 回收商首页统计：从后端拉可见询价 + 我的报价 + 我的订单
async function loadRecyclerHomeData() {
  inquiryList.value = []
  try {
    const [inqRes, quoteRes, orderRes] = await Promise.all([
      getRecyclerInquiries(),
      getMyQuotes().catch(() => ({ list: [] })),
      getMyOrders().catch(() => ({ list: [] }))
    ])

    const quotesByInquiry = {}
    ;(quoteRes.list || []).forEach(q => {
      const mapped = {
        ...q,
        recyclerCompanyId: q.recycler_company_id || q.recyclerCompanyId,
        quoteUserId: q.recycler_id || q.quoteUserId,
        amount: q.price
      }
      ;(quotesByInquiry[q.inquiry_id] = quotesByInquiry[q.inquiry_id] || []).push(mapped)
    })

    const orderByInquiry = {}
    ;(orderRes.list || []).forEach(order => {
      orderByInquiry[order.inquiry_id] = order
    })

    inquiryList.value = (inqRes.list || []).map(item => {
      const mapped = {
        ...item,
        quotes: quotesByInquiry[item.id] || []
      }

      const order = orderByInquiry[item.id]
      if (order) {
        mapped.orderId = order.id
        mapped.tradeStatus = order.status
        mapped.status = 'accepted'
        mapped.quoteStatus = 'accepted'
        mapped.selectedRecyclerCompanyId = order.recycler_company_id
      }

      return mapped
    })
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  const local = uni.getStorageSync('inquiryList') || []
  inquiryList.value = local.map(item => ({
    ...item,
    quotes: Array.isArray(item.quotes) ? item.quotes : []
  }))
}

const companyFund = computed(() => {
  const companyId = Number(currentUser.value.company_id)

  const fund = fundList.value.find(item => {
    return Number(item.companyId) === companyId
  })

  if (fund) return fund

  return {
    companyId,
    companyName: currentUser.value.company_name || '',
    balance: 0,
    frozenAmount: 0,
    updatedTime: ''
  }
})

const canQuoteByFund = computed(() => {
  return Number(companyFund.value.balance || 0) >= 5000
})

const pendingAccountCount = computed(() => {
  return (accountState.value.accounts || []).filter(item => item.status === 'pending').length
})

const approvedAccountCount = computed(() => {
  return (accountState.value.accounts || []).filter(item => item.status === 'approved').length
})

const staffAccountCount = computed(() => {
  return (accountState.value.accounts || []).filter(item => {
    return item.role === 'merchant_staff' ||
      item.role === 'recycler_staff' ||
      item.role === 'recycler_keeper'
  }).length
})

const platformRechargePendingCount = computed(() => {
  return rechargeApplyList.value.filter(item => item.status === 'pending').length
})

const platformPaymentPendingCount = computed(() => {
  return inquiryList.value.filter(item => {
    return item.paymentStatus === 'pending' ||
      item.tradeStatus === 'payment_reviewing'
  }).length
})

const platformCancelPendingCount = computed(() => {
  return inquiryList.value.filter(item => item.cancelApplyStatus === 'pending').length
})

const platformPayMerchantCount = computed(() => {
  return inquiryList.value.filter(item => item.tradeStatus === 'recycler_received').length
})

const platformTradeCount = computed(() => platformTradeList.value.length)

const platformHasOrderCount = computed(() => {
  return platformTradeList.value.filter(item => !!item.order).length
})

const platformAppealCount = computed(() => {
  return platformTradeList.value.filter(item => {
    const status = getAdminTradeStatus(item)
    return status === 'appealing' || item.order?.status === 'appealing'
  }).length
})

const platformPendingTradeCount = computed(() => {
  return platformTradeList.value.filter(item => {
    const status = getAdminTradeStatus(item)
    return status === 'pending_quote' || status === 'quoted' || status === 'appealing'
  }).length
})

const platformCompletedOrderCount = computed(() => {
  return platformTradeList.value.filter(item => {
    const status = getAdminTradeStatus(item)
    return status === 'completed' || status === 'closed'
  }).length
})

const myRechargePendingCount = computed(() => {
  return rechargeApplyList.value.filter(item => {
    return Number(item.companyId) === Number(currentUser.value.company_id) &&
      item.status === 'pending'
  }).length
})

const merchantInquiryList = computed(() => {
  const user = currentUser.value

  return inquiryList.value.filter(item => {
    if (user.role === 'merchant_owner') {
      return Number(item.merchantCompanyId) === Number(user.company_id) ||
        Number(item.company_id) === Number(user.company_id)
    }

    if (user.role === 'merchant_staff') {
      return Number(item.merchantUserId) === Number(user.id) ||
        Number(item.merchant_id) === Number(user.id)
    }

    return false
  })
})

const merchantInquiryCount = computed(() => {
  return merchantInquiryList.value.length
})

const merchantQuotedCount = computed(() => {
  return merchantInquiryList.value.filter(item => {
    return getQuoteList(item).length > 0 && !isFinished(item)
  }).length
})

const merchantTradeTodoCount = computed(() => {
  return merchantInquiryList.value.filter(item => {
    // 后端订单状态：confirmed=待商家发货（需处理）；兼容旧 mock 名
    return item.tradeStatus === 'confirmed' ||
      item.tradeStatus === 'waiting_merchant_ship' ||
      item.tradeStatus === 'payment_rejected'
  }).length
})

const merchantFinishedCount = computed(() => {
  return merchantInquiryList.value.filter(item => {
    return isFinished(item)
  }).length
})

const recyclerWaitingCount = computed(() => {
  return inquiryList.value.filter(item => {
    return !isFinishedForRecycler(item) && !getMyQuote(item)
  }).length
})

const recyclerQuotedCount = computed(() => {
  return inquiryList.value.filter(item => {
    return !isFinishedForRecycler(item) && getMyQuote(item)
  }).length
})

const recyclerAcceptedCount = computed(() => {
  return inquiryList.value.filter(item => isAcceptedByMe(item)).length
})

const recyclerTodoTradeCount = computed(() => {
  return inquiryList.value.filter(item => {
    if (!isAcceptedByMe(item)) return false

    // 后端订单状态：shipped=待回收商收货（需处理）；兼容旧 mock 名
    return item.tradeStatus === 'shipped' ||
      item.tradeStatus === 'waiting_recycler_payment' ||
      item.tradeStatus === 'payment_rejected' ||
      item.tradeStatus === 'merchant_shipped'
  }).length
})

const tabs = computed(() => {
  let workbenchBadge = 0
  let orderBadge = 0

  if (currentUser.value.role === 'platform_admin') {
    workbenchBadge = platformAccountPending.value || pendingAccountCount.value
    orderBadge = platformPendingTradeCount.value
  } else if (isRecyclerRole(currentUser.value.role)) {
    orderBadge = recyclerTodoTradeCount.value + myRechargePendingCount.value
  } else if (isMerchantRole(currentUser.value.role)) {
    orderBadge = 0
  }

  return [
    {
      key: 'workbench',
      name: '工作台',
      icon: '⌂',
      badge: workbenchBadge
    },
    {
      key: 'orders',
      name: '订单',
      icon: '▤',
      badge: orderBadge
    },
    {
      key: 'mine',
      name: '我的',
      icon: '●',
      badge: 0
    }
  ]
})

const bottomTabs = computed(() => {
  let orderBadge = 0

  if (currentUser.value.role === 'platform_admin') {
    orderBadge = platformPendingTradeCount.value
  } else if (isRecyclerRole(currentUser.value.role)) {
    orderBadge = recyclerTodoTradeCount.value + myRechargePendingCount.value
  } else if (isMerchantRole(currentUser.value.role)) {
    orderBadge = 0
  }

  return [
    {
      key: 'workbench',
      name: '工作台',
      icon: buildNavIcon('workbench', NAV_COLOR.normal),
      activeIcon: buildNavIcon('workbench', NAV_COLOR.active),
      badge: currentUser.value.role === 'platform_admin' ? (platformAccountPending.value || pendingAccountCount.value) : 0
    },
    {
      key: 'orders',
      name: '订单',
      icon: buildNavIcon('orders', NAV_COLOR.normal),
      activeIcon: buildNavIcon('orders', NAV_COLOR.active),
      badge: orderBadge
    },
    {
      key: 'mine',
      name: '我的',
      icon: buildNavIcon('mine', NAV_COLOR.normal),
      activeIcon: buildNavIcon('mine', NAV_COLOR.active),
      badge: 0
    }
  ]
})

const avatarText = computed(() => {
  const role = currentUser.value.role

  if (role === 'platform_admin') return '管'
  if (role === 'merchant_owner') return '商'
  if (role === 'merchant_staff') return '员'
  if (role === 'recycler_owner') return '收'
  if (role === 'recycler_keeper') return '库'
  if (role === 'recycler_staff') return '抢'

  const name = currentUser.value.username || '账'
  return name.slice(0, 1)
})

const todayStats = computed(() => {
  const role = currentUser.value.role

  if (isMerchantRole(role)) {
    return {
      todo: merchantInquiryCount.value,
      done: merchantFinishedCount.value,
      todoLabel: '询价单',
      doneLabel: '已结束'
    }
  }

  if (isRecyclerRole(role)) {
    return {
      todo: recyclerWaitingCount.value,
      done: recyclerQuotedCount.value,
      todoLabel: '待报价',
      doneLabel: '已报价'
    }
  }

  if (role === 'platform_admin') {
    return {
      todo: platformAccountPending.value || pendingAccountCount.value,
      done: platformTradeCount.value,
      todoLabel: '账号待审',
      doneLabel: '交易主线'
    }
  }

  return {
    todo: 0,
    done: 0,
    todoLabel: '待处理',
    doneLabel: '已完成'
  }
})

const menuListRaw = computed(() => {
  const user = currentUser.value

  if (user.role === 'merchant_owner') {
    return [
      {
        title: '设备极速询价',
        desc: '发布设备信息，向回收商发起报价申请',
        icon: '业务',
        url: '/pages/merchant/device/device',
        primary: true,
        colorClass: 'orange'
      },
      {
        title: '我的订单',
        desc: `待报价/待发货/待收货/已结束，当前 ${merchantQuotedCount.value} 条有报价`,
        icon: '业务',
        url: '/pages/merchant/order/order',
        colorClass: 'blue'
      },
      {
        title: '公司资料 / 员工权限',
        desc: '维护商家资料，管理员工操作权限',
        icon: '业务',
        url: '/pages/merchant/auth/auth',
        colorClass: 'gray'
      },
      {
        title: '员工账号',
        desc: '查看本公司全部员工账号与权限',
        icon: '业务',
        url: '/pages/company/staff-list/staff-list',
        colorClass: 'blue'
      },
      {
        title: '我的钱包',
        desc: '设置自己的分成比例，查看员工分成',
        icon: '业务',
        url: '/pages/merchant/commission/commission',
        colorClass: 'blue'
      },
      {
        title: '数据分析',
        desc: '查看成交金额、抽成构成与员工业绩',
        icon: '业务',
        url: '/pages/merchant/analysis/analysis',
        colorClass: 'gray'
      }
    ]
  }

  if (user.role === 'merchant_staff') {
    return [
      {
        title: '设备极速询价',
        desc: user.can_create_inquiry ? '发布设备并发起询价' : '当前账号暂无发起询价权限',
        icon: user.can_create_inquiry ? '询' : '锁',
        url: '/pages/merchant/device/device',
        primary: true,
        disabled: !user.can_create_inquiry,
        colorClass: user.can_create_inquiry ? 'orange' : 'gray'
      },
      {
        title: '我的订单',
        desc: `待报价/待发货/待收货/已结束，当前 ${merchantQuotedCount.value} 条有报价`,
        icon: '业务',
        url: '/pages/merchant/order/order',
        colorClass: 'blue'
      },
      {
        title: '我的数据分析',
        desc: '查看自己的成交金额与业绩',
        icon: '业务',
        url: '/pages/merchant/analysis/analysis',
        colorClass: 'blue'
      },
      {
        title: '我的钱包',
        desc: '参与成交前请先设置',
        icon: '业务',
        url: '/pages/merchant/commission/commission',
        colorClass: 'gray'
      }
    ]
  }

  if (user.role === 'recycler_owner') {
    return [
      {
        title: '收到的询价',
        desc: `查看商家询价并管理员工报价，待报价 ${recyclerWaitingCount.value} 条`,
        icon: '业务',
        url: '/pages/recycler/inquiry/inquiry',
        primary: true,
        colorClass: 'orange'
      },
      {
        title: '回收订单',
        desc: `处理收货、验机与订单进度，进行中 ${recyclerTodoTradeCount.value} 条`,
        icon: '业务',
        url: '/pages/recycler/order/order',
        colorClass: 'green'
      },
      {
        title: '员工账号',
        desc: '查看本公司全部员工账号与权限',
        icon: '业务',
        url: '/pages/company/staff-list/staff-list',
        colorClass: 'gray'
      },
      {
        title: '数据分析',
        desc: '查看成交、扣款、资金池与员工报价成功率',
        icon: '业务',
        url: '/pages/recycler/analysis/analysis',
        colorClass: 'blue'
      }
    ]
  }

  if (user.role === 'recycler_keeper') {
    return [
      {
        title: '签收管理',
        desc: `处理设备收货与验机记录，待处理 ${recyclerTodoTradeCount.value} 条`,
        icon: '业务',
        url: '/pages/recycler/order/order',
        primary: true,
        colorClass: 'green'
      },
      {
        title: '全部订单数据',
        desc: '查看公司全部订单与交易数据',
        icon: '业务',
        url: '/pages/recycler/order/order',
        colorClass: 'blue'
      },
      {
        title: '数据分析',
        desc: '查看成交、扣款、资金池与员工报价成功率',
        icon: '业务',
        url: '/pages/recycler/analysis/analysis',
        colorClass: 'gray'
      }
    ]
  }

  if (user.role === 'recycler_staff') {
    return [
      {
        title: '抢单报价',
        desc: `查看商家询价并提交报价，当前待报价 ${recyclerWaitingCount.value} 条`,
        icon: '业务',
        url: '/pages/recycler/inquiry/inquiry',
        primary: true,
        colorClass: 'orange'
      },
      {
        title: '我负责的订单',
        desc: `查看自己报价、接单和收货流程，待处理 ${recyclerTodoTradeCount.value} 条`,
        icon: '业务',
        url: '/pages/recycler/order/order',
        colorClass: 'green'
      },
      {
        title: '单号查询报价',
        desc: '凭订单号查询同事报价与成交状态',
        icon: '业务',
        url: '/pages/recycler/quote-search/quote-search',
        colorClass: 'blue'
      },
      {
        title: '我的数据分析',
        desc: '查看自己的报价成功率与成交统计',
        icon: '业务',
        url: '/pages/recycler/analysis/analysis',
        colorClass: 'gray'
      }
    ]
  }

  if (user.role === 'platform_admin') {
    return [
      {
        title: '审核中心',
        desc: `账号审核，当前待审 ${platformAccountPending.value || pendingAccountCount.value} 条`,
        icon: '业务',
        url: '/pages/platform/payment/payment',
        primary: true,
        colorClass: 'cyan',
        badge: platformAccountPending.value || pendingAccountCount.value
      },
      {
        title: '订单监控',
        desc: `查看全部交易主线与申诉，共 ${platformTradeCount.value} 条`,
        icon: '业务',
        url: '/pages/platform/orders/orders',
        colorClass: 'green'
      },
      {
        title: '资金池管理',
        desc: '直接设置各回收商资金池余额',
        icon: '业务',
        url: '/pages/platform/fund/fund',
        colorClass: 'blue'
      },
      {
        title: '数据总览',
        desc: '资金池与流水统计',
        icon: '业务',
        url: '/pages/platform/dashboard/dashboard',
        colorClass: 'cyan'
      },
      {
        title: '财务流水明细',
        desc: '逐条查看充值、冻结、释放与扣款',
        icon: '业务',
        url: '/pages/platform/finance/finance',
        colorClass: 'blue'
      }
    ]
  }

  return []
})

// 入口级权限:按统一权限表过滤工作台菜单(无权访问的页面不展示入口)
const menuList = computed(() => {
  const list = menuListRaw.value.filter(item => canAccessPage(currentUser.value, item.url)).map(item => {
    if (item.title === '我的订单' && isMerchantRole(currentUser.value.role)) {
      return { ...item, url: item.url + '?customer=1', badge: merchantQuotedCount.value + merchantTradeTodoCount.value }
    }
    if (item.title === '抢单报价' || (item.url === '/pages/recycler/inquiry/inquiry' && isRecyclerRole(currentUser.value.role))) {
      return { ...item, badge: recyclerWaitingCount.value }
    }
    return item
  })
  if(currentUser.value.role==='recycler_owner')list.push({title:'收货资料',url:'/pages/profile/profile',icon:'业务',colorClass:'blue'})
  // 所有角色都显示「联系客服」卡片
  list.push({
    title: '联系客服',
    icon: '业务',
    colorClass: 'blue',
    action: 'customerService'
  })
  return list
})

const dataCards = computed(() => {
  const user = currentUser.value

  if (user.role === 'platform_admin') {
    return [
      { label: '账号待审核', value: platformAccountPending.value || pendingAccountCount.value },
      { label: '全部交易', value: platformTradeCount.value },
      { label: '已生成订单', value: platformHasOrderCount.value },
      { label: '申诉订单', value: platformAppealCount.value },
      { label: '待处理', value: platformPendingTradeCount.value },
      { label: '已完成/关闭', value: platformCompletedOrderCount.value },
      { label: '已通过账号', value: approvedAccountCount.value }
    ]
  }

  if (isRecyclerRole(user.role)) {
    return [
      { label: '待报价', value: recyclerWaitingCount.value },
      { label: '已报价', value: recyclerQuotedCount.value },
      { label: '已接单', value: recyclerAcceptedCount.value },
      { label: '进行中', value: recyclerTodoTradeCount.value }
    ]
  }

  if (isMerchantRole(user.role)) {
    return [
      { label: '我的询价', value: merchantInquiryCount.value },
      { label: '收到报价', value: merchantQuotedCount.value },
      { label: '订单待处理', value: merchantTradeTodoCount.value },
      { label: '已结束', value: merchantFinishedCount.value }
    ]
  }

  return [
    { label: '待处理', value: 0 },
    { label: '已完成', value: 0 },
    { label: '报价中', value: 0 },
    { label: '全部订单', value: 0 }
  ]
})

const homeOrderCards = computed(() => {
  const user = currentUser.value

  if (isRecyclerRole(user.role)) {
    return inquiryList.value.map(item => {
      const myQuote = getMyQuote(item)
      const status = getRecyclerHomeStatus(item)

      return {
        id: item.id,
        shop: item.merchantCompanyName || item.company_name || '商家公司',
        time: item.createTime || item.created_at || '-',
        device: getDeviceTitle(item),
        desc: myQuote
          ? `我的报价 ¥${myQuote.amount}，${status.text}`
          : `${item.storage || '-'}，${status.text}`,
        icon: getDeviceIcon(item),
        statusClass: status.className,
        statusText: status.text,
        url: getRecyclerCardUrl(item)
      }
    })
  }

  if (isMerchantRole(user.role)) {
    return merchantInquiryList.value.map(item => {
      const quoteCount = getQuoteList(item).length
      const status = getMerchantHomeStatus(item)

      return {
        id: item.id,
        shop: currentUser.value.company_name || '我的公司',
        time: item.createTime || item.created_at || '-',
        device: getDeviceTitle(item),
        desc: `${item.storage || '-'}，${status.text}`,
        icon: getDeviceIcon(item),
        statusClass: status.className,
        statusText: status.text,
        url: '/pages/merchant/order/order'
      }
    })
  }

  if (user.role === 'platform_admin') {
    return platformAdminCards.value
  }

  return []
})

const platformAdminCards = computed(() => {
  const cards = []

  platformTradeList.value.slice(0, 8).forEach(trade => {
    const status = getAdminTradeStatus(trade)
    const orderNo = trade.orderNo || trade.order?.order_no || trade.order?.orderNo || ''
    const quoteCount = trade.quoteCount || (trade.quotes || []).length

    cards.push({
      id: `trade-${trade.id}`,
      shop: trade.merchantCompanyName || trade.merchant?.company_name || '商家',
      time: trade.createTime || '-',
      device: getPlatformTradeDeviceTitle(trade),
      desc: `${getTradeFlowStatusLabel(status)} · 报价 ${quoteCount} · ${orderNo || '暂未生成订单'}`,
      icon: orderNo ? '单' : '询',
      statusClass: status === 'appealing'
        ? 'pending'
        : (status === 'completed'
          ? 'done'
          : (status === 'closed'
            ? 'pending'
            : (status === 'pending_quote' || status === 'quoted' ? 'waiting' : 'processing'))),
      statusText: getTradeFlowStatusLabel(status),
      url: '/pages/platform/orders/orders'
    })
  })

  cards.push({
    id: 'monitor',
    shop: '订单监控',
    time: '平台管理',
    device: '进入订单监控',
    desc: `全部 ${platformTradeCount.value} 条 · 已生成订单 ${platformHasOrderCount.value} 条 · 待处理 ${platformPendingTradeCount.value} 条`,
    icon: '👁',
    statusClass: 'processing',
    statusText: '查看全部',
    url: '/pages/platform/orders/orders'
  })

  return cards.slice(0, 12)
})

const permissionSummary = computed(() => {
  const role = currentUser.value.role

  const map = {
    platform_admin: '平台全部权限',
    merchant_owner: '商家全部权限',
    merchant_staff: '商家员工权限',
    recycler_owner: '回收商全部权限',
    recycler_keeper: '库管权限',
    recycler_staff: '员工个人数据权限'
  }

  return map[role] || '-'
})

function refreshCurrentUser() {
  currentUser.value = uni.getStorageSync('currentUser') ||
    uni.getStorageSync('userInfo') ||
    {}
  accountState.value = getAccountState()

  const list = uni.getStorageSync('inquiryList') || []
  inquiryList.value = list.map(item => {
    return {
      ...item,
      quotes: Array.isArray(item.quotes) ? item.quotes : []
    }
  })

  fundList.value = uni.getStorageSync(FUND_KEY) || []
  rechargeApplyList.value = uni.getStorageSync(RECHARGE_KEY) || []

  ensureRecyclerFund()
}

async function loadPlatformData() {
  if (currentUser.value.role !== 'platform_admin') return

  try {
    const res = await getAdminTrades()
    platformTradeList.value = normalizeAdminTradeList(res)
  } catch (error) {
    try {
      const res = await getMyOrders()
      platformTradeList.value = ordersToAdminTradeFallback(res)
    } catch (fallbackError) {
      platformTradeList.value = []
    }
  }

  try {
    const res = await getPendingAccounts()
    const list = Array.isArray(res)
      ? res
      : (res?.list || res?.items || res?.data || [])

    platformAccountPending.value = list.length
  } catch (error) {
    platformAccountPending.value = pendingAccountCount.value
  }
}

function getPlatformTradeDeviceTitle(trade) {
  const title = `${trade.brand || trade.device?.brand || ''} ${trade.model || trade.device?.model || ''}`.trim()
  return title || '设备'
}

function ensureRecyclerFund() {
  if (!isRecyclerRole(currentUser.value.role)) return

  const companyId = Number(currentUser.value.company_id)
  if (!companyId) return

  const existed = fundList.value.find(item => Number(item.companyId) === companyId)

  if (existed) return

  fundList.value.unshift({
    companyId,
    companyName: currentUser.value.company_name || `中晨回收${companyId}`,
    balance: 0,
    frozenAmount: 0,
    updatedTime: getNowText()
  })

  uni.setStorageSync(FUND_KEY, fundList.value)
}

function handleMenu(item) {
  if (item.action === 'customerService') {
    openCustomerService()
    return
  }

  if (item.disabled) {
    uni.showToast({
      title: '暂无权限',
      icon: 'none'
    })
    return
  }

  go(item.url)
}

function handleBottomTab(tab) {
  if (tab.key === 'message') {
    uni.navigateTo({
      url: '/pages/message/message'
    })
    return
  }

  activeTab.value = tab.key
}

function go(url) {
  if (!url) {
    uni.showToast({
      title: '页面暂未配置',
      icon: 'none'
    })
    return
  }

  uni.navigateTo({
    url,
    fail: () => {
      uni.showToast({
        title: '页面暂未创建',
        icon: 'none'
      })
    }
  })
}

function refreshPage() {
  refreshCurrentUser()
  loadPlatformData()

  uni.showToast({
    title: '已刷新',
    icon: 'success'
  })
}

function openPasswordPopup() {
  passwordForm.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  passwordPopupVisible.value = true
}

// 联系客服：弹出管理员电话，可一键拨打
function openCustomerService() {
  const phone = '18280712621'
  uni.showModal({
    title: '联系客服',
    content: `客服/管理员电话：${phone}`,
    confirmText: '拨打',
    cancelText: '关闭',
    confirmColor: '#4b5563',
    success: (res) => {
      if (res.confirm) {
        uni.makePhoneCall({ phoneNumber: phone })
      }
    }
  })
}

function closePasswordPopup() {
  passwordPopupVisible.value = false
}

async function submitPassword() {
  const { oldPassword, newPassword, confirmPassword } = passwordForm.value

  if (!oldPassword) {
    uni.showToast({ title: '请输入原密码', icon: 'none' })
    return
  }

  if (!newPassword || newPassword.length < 3) {
    uni.showToast({ title: '新密码至少3位', icon: 'none' })
    return
  }

  if (newPassword === oldPassword) {
    uni.showToast({ title: '新密码不能与原密码相同', icon: 'none' })
    return
  }

  if (newPassword !== confirmPassword) {
    uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' })
    return
  }

  try {
    await changePasswordApi({
      old_password: oldPassword,
      new_password: newPassword
    })
  } catch (error) {
    return
  }

  closePasswordPopup()

  uni.showModal({
    title: '修改成功',
    content: '密码已更新，请使用新密码重新登录。',
    showCancel: false,
    confirmText: '重新登录',
    success: () => {
      clearAccountSession()
      uni.reLaunch({ url: '/pages/login/login' })
    }
  })
}

function logout() {
  uni.showModal({
    title: '确认退出',
    content: '确定要退出当前账号吗？',
    confirmColor: '#4b5563',
    success: res => {
      if (res.confirm) {
        clearAccountSession()

        uni.reLaunch({
          url: '/pages/login/login'
        })
      }
    }
  })
}

function isRecyclerRole(role) {
  return role === 'recycler_owner' ||
    role === 'recycler_keeper' ||
    role === 'recycler_staff'
}

function isMerchantRole(role) {
  return role === 'merchant_owner' ||
    role === 'merchant_staff'
}

function getQuoteList(item) {
  return Array.isArray(item.quotes) ? item.quotes : []
}

function getMyQuote(item) {
  return getQuoteList(item).find(quote => {
    return Number(quote.recyclerCompanyId) === Number(currentUser.value.company_id)
  })
}

function isOffShelf(item) {
  return item.status === '商家已下架' || item.quoteStatus === 'off_shelf'
}

function isAccepted(item) {
  return item.status === '商家已接单' || item.quoteStatus === 'accepted'
}

function isFinished(item) {
  if (item.status === 'expired' || item.can_quote === false) return true
  return item.status === '商家已接单' ||
    item.status === '商家已下架' ||
    item.status === '交易完成' ||
    item.status === '订单已取消' ||
    item.quoteStatus === 'accepted' ||
    item.quoteStatus === 'off_shelf' ||
    item.quoteStatus === 'done' ||
    item.quoteStatus === 'cancelled'
}

function isAcceptedByMe(item) {
  return isAccepted(item) &&
    Number(item.selectedRecyclerCompanyId) === Number(currentUser.value.company_id)
}

function isAcceptedByOther(item) {
  return isAccepted(item) &&
    item.selectedRecyclerCompanyId &&
    Number(item.selectedRecyclerCompanyId) !== Number(currentUser.value.company_id)
}

function isFinishedForRecycler(item) {
  if (item.status === 'expired' || item.can_quote === false) return true
  return isOffShelf(item) || isAcceptedByMe(item) || isAcceptedByOther(item)
}

function getRecyclerHomeStatus(item) {
  if (isOffShelf(item)) {
    return { text: '商家已下架', className: 'off' }
  }

  if (isAcceptedByOther(item)) {
    return { text: '被其他回收商完成', className: 'off' }
  }

  const status = resolveItemTradeStatus(item)

  return {
    text: getTradeFlowStatusLabel(status),
    className: getTradeFlowStatusClassName(status)
  }
}

function getMerchantHomeStatus(item) {
  if (isOffShelf(item)) {
    return { text: '已下架', className: 'off' }
  }

  const status = resolveItemTradeStatus(item)

  return {
    text: getTradeFlowStatusLabel(status),
    className: getTradeFlowStatusClassName(status)
  }
}

function getRecyclerCardUrl(item) {
  if (isAcceptedByMe(item) || item.tradeStatus) {
    return '/pages/recycler/order/order'
  }

  return '/pages/recycler/inquiry/inquiry'
}

function getDeviceIcon(item) {
  const type = item.deviceType || item.device_type || ''

  if (type.includes('平板')) return '板'
  if (type.includes('电脑')) return '脑'
  if (type.includes('手机')) return '机'

  return '设'
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

  return map[role] || role || '未登录'
}

function companyTypeText(type) {
  const map = {
    merchant: '商家',
    recycler: '回收商',
    platform: '平台'
  }

  return map[type] || '-'
}

function accountStatusText(status) {
  const map = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已驳回'
  }

  return map[status] || '-'
}

function formatShortMoney(value) {
  const num = Number(value || 0)

  if (num >= 10000) {
    return `${(num / 10000).toFixed(1)}万`
  }

  return String(Math.round(num))
}
</script>




<style scoped>
.entry-count{display:inline-block;margin-left:12rpx;min-width:32rpx;height:32rpx;line-height:32rpx;text-align:center;border-radius:16rpx;background:#ef4444;color:#fff;font-size:24rpx;padding:0 6rpx;}

/* ==========================================================================
   1. 全局底色与状态栏安全垫高
   ========================================================================== */
.page {
  min-height: 100vh;
  background: #f5f7fa; 
  padding-bottom: calc(160rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
}
.status-bar-placeholder {
  height: var(--status-bar-height);
  min-height: 44rpx;
  background: #1e293b;
}
.hero {
  padding: 60rpx 36rpx 130rpx;
  background: #17324d;
  color: #ffffff;
  border-radius: 0 0 54rpx 54rpx;
  box-shadow: none;
}
.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hello {
  font-size: 26rpx;
  opacity: 0.75;
  margin-bottom: 18rpx;
  letter-spacing: 2rpx;
}
.title {
  font-size: 46rpx;
  font-weight: 600;
  letter-spacing: 2rpx;
  line-height: 1.3;
}
.hero-actions {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-top: 8rpx;
}
/* 右上角胶囊按钮组 — 仿乐回收样式 */
.action-pill {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 999rpx;
  overflow: hidden;
  box-shadow: none;
}
.action-btn {
  width: 76rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  color: #4a5568;
  font-weight: 500;
}
.action-btn:active {
  background: rgba(0, 0, 0, 0.06);
}
.action-sep {
  width: 1rpx;
  height: 26rpx;
  background: #e2e8f0;
}
.search-card {
  display: flex;
  align-items: center;
  margin-top: 48rpx;
  height: 84rpx;
  padding: 0 32rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
  border: 1rpx solid rgba(255, 255, 255, 0.1);
  box-sizing: border-box;
}
.search-icon { width: 36rpx; height: 36rpx; margin-right: 14rpx; font-size: 26rpx; display: flex; align-items: center; opacity: 0.9; }
.search-text { flex: 1; font-size: 24rpx; font-weight: 500; letter-spacing: 1rpx; }
@keyframes breathing {
  0% { box-shadow: none; }
  50% { box-shadow: none; }
  100% { box-shadow: none; }
}
.search-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: #10b981; animation: breathing 2s infinite ease-in-out; }
.stats-row { display: flex; align-items: center; margin-top: 52rpx; padding: 10rpx 0 0; }
.stat-item { flex: 1; text-align: center; }
.stat-number { font-size: 52rpx; font-weight: 600; letter-spacing: -1rpx; line-height: 1.1; }
.stat-label { margin-top: 14rpx; font-size: 24rpx; opacity: 0.7; }
.stat-line { width: 1rpx; height: 44rpx; background: rgba(255, 255, 255, 0.15); }
.content { margin-top: -60rpx; padding: 0 30rpx; box-sizing: border-box; }
.filter-row { display: flex; gap: 20rpx; margin-bottom: 28rpx; }
.filter-pill {
  flex: 1; height: 76rpx; line-height: 76rpx; padding: 0 28rpx;
  border-radius: 20rpx; background: #ffffff; color: #1e293b;
  font-size: 25rpx; font-weight: 600; box-sizing: border-box;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: none;
  border: 1rpx solid rgba(241, 245, 249, 0.8);
}
.filter-arrow { color: #64748b; font-size: 24rpx; margin-left: 8rpx; }
.section-row {
  display: flex; align-items: center; justify-content: space-between;
  background: #ffffff; margin: 0;
  padding: 38rpx 32rpx 20rpx 32rpx;
  border-radius: 16rpx 32rpx 0 0;
  border-bottom: 1rpx solid #f8fafc;
}
.menu-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 40rpx 10rpx; background: #ffffff;
  padding: 24rpx 20rpx 44rpx;
  border-radius: 0 0 32rpx 32rpx;
  box-shadow: none;
}
.section-title {
  color: #1e293b; font-size: 28rpx; font-weight: 600;
  letter-spacing: 0.5rpx; position: relative; padding-left: 18rpx;
}
.section-title::before {
  content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 6rpx; height: 24rpx;
  background: #17324d;
  border-radius: 4rpx;
}
.section-more { color: #64748b; font-size: 24rpx; font-weight: 500; }
.menu-item { display: flex; flex-direction: column; align-items: center; gap: 14rpx; }
.menu-item.disabled { opacity: 0.35; }
.menu-item:active { transform: scale(0.93); }
.menu-icon-wrap { position: relative; width: 106rpx; height: 106rpx; border-radius: 16rpx; display: flex; align-items: center; justify-content: center; }
.menu-icon-text { font-size: 50rpx; line-height: 1; }
.menu-badge { position: absolute; top: -6rpx; right: -6rpx; min-width: 32rpx; height: 32rpx; padding: 0 6rpx; border-radius: 999rpx; background: #ef4444; color: #ffffff; font-size: 24rpx; font-weight: bold; line-height: 30rpx; text-align: center; border: 2rpx solid #ffffff; box-shadow: none; box-sizing: border-box; }
.menu-label { font-size: 24rpx; color: #334155; text-align: center; line-height: 1.3; font-weight: 600; }
.orange { background: #17324d; }
.blue   { background: #17324d; }
.green  { background: #17324d; }
.purple { background: #17324d; }
.gray   { background: #17324d; }
.cyan   { background: #17324d; }
.float-btn { position: fixed; right: 40rpx; bottom: calc(160rpx + env(safe-area-inset-bottom)); width: 96rpx; height: 96rpx; border-radius: 50%; background: #17324d; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 38rpx; box-shadow: none; z-index: 30; border: 1rpx solid rgba(255, 255, 255, 0.08); }
.float-btn:active { transform: scale(0.9); }
.fund-mini-card { margin-bottom: 24rpx; padding: 30rpx; border-radius: 16rpx; background: #ffffff; display: flex; justify-content: space-between; align-items: center; box-shadow: none; border: 1rpx solid rgba(241, 245, 249, 0.8); }
.fund-mini-label { color: #64748b; font-size: 24rpx; font-weight: 500; }
.fund-mini-money { margin-top: 6rpx; color: #ef4444; font-size: 42rpx; font-weight: 600; }
.fund-mini-status { padding: 8rpx 20rpx; border-radius: 999rpx; font-size: 24rpx; font-weight: bold; }
.fund-mini-status.safe { background: #ecfdf5; color: #059669; }
.fund-mini-status.danger { background: #fef2f2; color: #dc2626; }
.tabs-card { display: flex; align-items: center; height: 92rpx; padding: 8rpx; border-radius: 999rpx; background: #ffffff; box-shadow: none; box-sizing: border-box; }
.tab-item { position: relative; flex: 1; height: 76rpx; line-height: 76rpx; text-align: center; border-radius: 999rpx; color: #64748b; font-size: 26rpx; font-weight: bold; }
.tab-item.active { background: #1e293b; color: #ffffff; box-shadow: none; }
.tab-pane { padding-top: 60rpx; }
.badge { position: absolute; right: 18rpx; top: -6rpx; min-width: 36rpx; height: 36rpx; line-height: 36rpx; border-radius: 999rpx; background: #ef4444; color: #ffffff; font-size: 24rpx; font-weight: bold; }
.tab-pane { padding-top: 60rpx; }
.badge { position: absolute; right: 18rpx; top: -6rpx; min-width: 36rpx; height: 36rpx; line-height: 36rpx; border-radius: 999rpx; background: #ef4444; color: #ffffff; font-size: 24rpx; font-weight: bold; }
.tab-pane {
  padding-top: 60rpx;
}
.badge {
  position: absolute;
  right: 18rpx;
  top: -6rpx;
  min-width: 36rpx;
  height: 36rpx;
  line-height: 36rpx;
  border-radius: 999rpx;
  background: #ff4d4f;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: bold;
  box-shadow: none;
}
/* 筛选药丸 */
.filter-row {
  display: flex;
  gap: 20rpx;
  margin: 32rpx 0;
}
.filter-pill {
  flex: 1;
  height: 76rpx;
  line-height: 76rpx;
  padding: 0 28rpx;
  border-radius: 24rpx;
  background: #ffffff;
  color: #2d3748;
  font-size: 26rpx;
  font-weight: 600;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: none;
}
.filter-arrow {
  color: #64748b;
  font-size: 28rpx;
}
/* 资金池卡片 */
.fund-mini-card {
  margin-bottom: 32rpx;
  padding: 32rpx;
  border-radius: 16rpx;
  background: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: none;
}
.fund-mini-label { color: #718096; font-size: 24rpx; font-weight: 500; }
.fund-mini-money { margin-top: 10rpx; color: #ff4d4f; font-size: 48rpx; font-weight: 600; }
.fund-mini-status { padding: 12rpx 24rpx; border-radius: 999rpx; font-size: 24rpx; font-weight: bold; }
.fund-mini-status.safe { background: #f6ffed; color: #389e0d; border: 1rpx solid #b7eb8f; }
.fund-mini-status.danger { background: #fff1f0; color: #cf1322; border: 1rpx solid #ffa39e; }
/* 模块标题行 */
.section-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 40rpx 0 24rpx;
}
.section-title {
  color: #1a202c;
  font-size: 32rpx;
  font-weight: bold;
  letter-spacing: 0.5rpx;
  position: relative;
  padding-left: 18rpx;
}
.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 6rpx;
  height: 28rpx;
  background: #4a5568;
  border-radius: 4rpx;
}
.section-more { color: #64748b; font-size: 24rpx; }
/* 金刚区图标网格 */
.menu-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 44rpx 10rpx;
  padding: 40rpx 20rpx;
  background: #ffffff;
  border-radius: 16rpx;
  box-shadow: none;
}
.menu-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}
.menu-item.disabled { opacity: 0.35; }
.menu-item:active { transform: scale(0.92); }
.menu-icon-wrap {
  position: relative;
  width: 112rpx;
  height: 112rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: none;
}
.menu-icon-text { font-size: 52rpx; line-height: 1; }
.menu-badge {
  position: absolute;
  top: -6rpx; right: -6rpx;
  min-width: 32rpx; height: 32rpx;
  padding: 0 8rpx;
  border-radius: 999rpx;
  background: #ff4d4f;
  color: #ffffff;
  font-size: 24rpx; font-weight: bold;
  line-height: 32rpx; text-align: center;
  box-shadow: none;
}
.menu-label {
  font-size: 24rpx;
  color: #2d3748;
  text-align: center;
  line-height: 1.4;
  font-weight: 600;
}
.orange { background: #17324d; box-shadow: none; }
.blue   { background: #17324d; box-shadow: none; }
.green  { background: #17324d; box-shadow: none; }
.purple { background: #17324d; box-shadow: none; }
.gray   { background: #17324d; box-shadow: none; }
.cyan   { background: #17324d; box-shadow: none; }
/* 数据统计卡片 */
.data-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24rpx; }
.data-card { padding: 36rpx; border-radius: 16rpx; background: #ffffff; box-shadow: none; }
.data-number { color: #2d3748; font-size: 40rpx; font-weight: 600; word-break: break-all; }
.data-label { margin-top: 12rpx; color: #718096; font-size: 24rpx; font-weight: 500; }
.tips-card { margin-top: 32rpx; padding: 32rpx; border-radius: 16rpx; background: #ffffff; box-shadow: none; }
.tips-title { color: #1a202c; font-size: 30rpx; font-weight: bold; margin-bottom: 16rpx; }
.tips-line { color: #4a5568; font-size: 24rpx; line-height: 42rpx; }
.empty-card { padding: 90rpx 30rpx; border-radius: 16rpx; background: #ffffff; color: #64748b; text-align: center; font-size: 28rpx; box-shadow: none; }
/* 订单卡片 */
.order-card { padding: 32rpx; border-radius: 16rpx; background: #ffffff; margin-bottom: 24rpx; box-shadow: none; }
.order-head { display: flex; justify-content: space-between; align-items: center; padding-bottom: 24rpx; border-bottom: 1rpx solid #f1f3f7; }
.order-shop { color: #1a202c; font-size: 30rpx; font-weight: bold; }
.order-time { margin-top: 8rpx; color: #64748b; font-size: 24rpx; }
.order-status { height: 44rpx; line-height: 44rpx; padding: 0 20rpx; border-radius: 999rpx; color: #ffffff; font-size: 24rpx; font-weight: bold; }
.order-status.pending { background: #ff7875; }
.order-status.processing { background: #4a5568; }
.order-status.done { background: #52c41a; }
.order-body { display: flex; align-items: center; padding-top: 24rpx; }
.device-thumb { width: 96rpx; height: 76rpx; margin-right: 24rpx; border-radius: 16rpx; background: #f7fafc; color: #4a5568; display: flex; align-items: center; justify-content: center; font-size: 32rpx; font-weight: bold; }
.device-info { flex: 1; }
.device-name { color: #1a202c; font-size: 28rpx; font-weight: bold; margin-bottom: 8rpx; }
.device-desc { color: #718096; font-size: 24rpx; }
.order-action { width: 120rpx; height: 64rpx; line-height: 64rpx; text-align: center; border-radius: 999rpx; background: #2d3748; color: #ffffff; font-size: 24rpx; font-weight: bold; box-shadow: none; }
.end-text { margin-top: 40rpx; text-align: center; color: #64748b; font-size: 24rpx; }
/* 个人中心 */
.profile-card, .info-card { padding: 36rpx; border-radius: 16rpx; background: #ffffff; box-shadow: none; margin-top: 32rpx; }
.profile-card { display: flex; align-items: center; }
.profile-avatar { width: 108rpx; height: 108rpx; margin-right: 24rpx; border-radius: 16rpx; background: #2d3748; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 42rpx; font-weight: bold; box-shadow: none; }
.profile-main { flex: 1; }
.profile-name { color: #1a202c; font-size: 36rpx; font-weight: bold; margin-bottom: 8rpx; }
.profile-role { color: #718096; font-size: 24rpx; }
.info-row { display: flex; justify-content: space-between; padding: 24rpx 0; border-bottom: 1rpx solid #f1f3f7; color: #4a5568; font-size: 26rpx; }
.info-row:last-child { border-bottom: none; }
.logout-btn { margin-top: 40rpx; height: 96rpx; line-height: 96rpx; border-radius: 999rpx; background: #ffffff; color: #ff4d4f; font-size: 30rpx; font-weight: bold; box-shadow: none; }
.logout-btn::after { border: none; }
.account-actions { margin-top: 32rpx; padding: 8rpx 36rpx; border-radius: 16rpx; background: #ffffff; box-shadow: none; }
.account-row { display: flex; justify-content: space-between; align-items: center; padding: 32rpx 0; border-bottom: 1rpx solid #f1f3f7; }
.account-row:last-child { border-bottom: none; }
.account-title { color: #1a202c; font-size: 30rpx; font-weight: bold; }
.account-desc { margin-top: 8rpx; color: #718096; font-size: 24rpx; }
.account-arrow { color: #cbd5e0; font-size: 44rpx; font-weight: 300; }
/* 弹窗 */
.mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5);  z-index: 99; display: flex; align-items: center; justify-content: center; padding: 40rpx; box-sizing: border-box; }
.popup { width: 100%; padding: 44rpx 40rpx; border-radius: 16rpx; background: #ffffff; box-sizing: border-box; box-shadow: none; }
.popup-title { text-align: center; color: #1a202c; font-size: 36rpx; font-weight: bold; }
.popup-desc { margin-top: 14rpx; text-align: center; color: #718096; font-size: 26rpx; }
.pwd-item { margin-top: 32rpx; }
.pwd-label { margin-bottom: 14rpx; color: #4a5568; font-size: 26rpx; font-weight: bold; }
.pwd-input { height: 90rpx; padding: 0 28rpx; border-radius: 24rpx; background: #f7fafc; font-size: 28rpx; box-sizing: border-box; border: 1rpx solid #edf2f7; }
.popup-actions { display: flex; gap: 20rpx; margin-top: 44rpx; }
.popup-btn { flex: 1; height: 88rpx; line-height: 88rpx; text-align: center; border-radius: 999rpx; font-size: 28rpx; font-weight: bold; }
.popup-btn.cancel { background: #edf2f7; color: #4a5568; }
.popup-btn.confirm { background: #2d3748; color: #ffffff; box-shadow: none; }
/* 底部导航 */
.bottom-nav { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; height: calc(112rpx + env(safe-area-inset-bottom)); padding-bottom: env(safe-area-inset-bottom); background: rgba(255,255,255,0.95);  display: flex; box-shadow: none; }
.nav-item { position: relative; flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8rpx; color: #64748b; }
.nav-item.active { color: #2d3748; }
.nav-icon { width: 48rpx; height: 48rpx; }
.nav-text { font-size: 24rpx; font-weight: 600; }
.nav-badge { position: absolute; top: 10rpx; right: 44rpx; min-width: 32rpx; height: 32rpx; line-height: 32rpx; border-radius: 999rpx; background: #ff4d4f; color: #ffffff; font-size: 24rpx; font-weight: bold; text-align: center; padding: 0 8rpx; box-sizing: border-box; box-shadow: none; }
/* 悬浮球 */
.float-btn { position: fixed; right: 40rpx; bottom: calc(160rpx + env(safe-area-inset-bottom)); width: 104rpx; height: 104rpx; border-radius: 50%; background: #17324d; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 44rpx; box-shadow: none; z-index: 30; }
.float-btn:active { transform: scale(0.92); }
.menu-card:active, .order-card:active, .data-card:active, .nav-item:active { transform: scale(0.98); opacity: 0.9; }





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



.page .hero{margin:0;padding:calc(var(--status-bar-height) + 44rpx) 32rpx 36rpx;border-radius:0;background:#17324d}
.hero .hello{font-size:26rpx;opacity:1;color:#dce7f0;margin-bottom:8rpx}
.hero .title{font-size:40rpx;letter-spacing:0;font-weight:600}
.hero .search-card{margin-top:28rpx;height:84rpx;border-radius:12rpx;background:#fff;color:#17324d;border:0;padding:0 24rpx}
.search-card .search-icon{width:32rpx;height:32rpx;opacity:1}
.search-arrow{font-size:36rpx;color:#64748b}
.hero .stats-row{margin-top:28rpx;padding:0}
.stat-number{font-size:44rpx}.hero .stat-label{opacity:1;color:#dce7f0;font-size:24rpx}
.page .content{margin-top:0;padding:0 24rpx}
.content .filter-row{margin:20rpx 0;gap:12rpx}.filter-pill{box-shadow:none;border-radius:8rpx;height:64rpx;font-size:24rpx;border:1rpx solid #e2e8f0}
.content .section-row{margin:0;padding:28rpx 24rpx 12rpx;border-radius:16rpx 16rpx 0 0;border:0}
.section-title{padding-left:0;font-size:30rpx}.section-title::before{display:none}
.content .menu-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12rpx;padding:12rpx 20rpx 24rpx;border-radius:0 0 16rpx 16rpx}
.menu-grid .menu-item{flex-direction:row;justify-content:flex-start;gap:16rpx;padding:20rpx 12rpx;background:#f7f9fb;border-radius:10rpx;min-width:0}
.menu-item .menu-icon-wrap{width:56rpx;height:56rpx;border-radius:8rpx;background:#e9eff5;flex-shrink:0}
.menu-icon{width:32rpx;height:32rpx}.menu-item .menu-label{text-align:left;font-size:26rpx;line-height:1.5;color:#17324d}
.page .float-btn{width:76rpx;height:76rpx;right:24rpx;font-size:32rpx;background:#17324d;box-shadow:none}
.page .tab-pane{padding-top:24rpx}.page .bottom-nav{box-shadow:none;border-top:1rpx solid #e2e8f0;background:#fff}

</style>
