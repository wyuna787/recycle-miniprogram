<template>
  <view class="page">
    <custom-navbar title="消息中心" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">{{ currentUser.username || '用户' }}</view>
          <view class="title">消息通知</view>
          <view class="desc">
            系统会根据订单、审核、付款、发货和打款状态自动生成提醒。
          </view>
        </view>

        <view class="hero-icon">信</view>
      </view>

      <view class="stats">
        <view class="stat-item">
          <view class="stat-number">{{ unreadCount }}</view>
          <view class="stat-label">重点提醒</view>
        </view>

        <view class="stat-item">
          <view class="stat-number">{{ messageList.length }}</view>
          <view class="stat-label">全部消息</view>
        </view>

        <view class="stat-item">
          <view class="stat-number">{{ todayCount }}</view>
          <view class="stat-label">今日消息</view>
        </view>
      </view>
    </view>

    <view class="tabs">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab', activeTab === tab.key ? 'active' : '']"
        @click="activeTab = tab.key"
      >
        {{ tab.name }}
        <text v-if="tab.badge" class="tab-badge">{{ tab.badge }}</text>
      </view>
    </view>

    <view class="tool-row">
      <view class="tool-btn" @click="refreshPage">
        刷新消息
      </view>

      <view class="tool-btn light" @click="goHome">
        返回工作台
      </view>
    </view>

    <view v-if="currentMessages.length === 0" class="empty">
      暂无消息
    </view>

    <view
      v-for="item in currentMessages"
      :key="item.id"
      :class="['message-card', item.important ? 'important' : '']"
    >
      <view class="message-head">
        <view :class="['message-icon', item.colorClass]">
          {{ item.icon }}
        </view>

        <view class="message-main">
          <view class="message-title">{{ item.title }}</view>
          <view class="message-time">{{ item.time || '-' }}</view>
        </view>

        <view :class="['message-tag', item.tagClass]">
          {{ item.tag }}
        </view>
      </view>

      <view class="message-content">
        {{ item.content }}
      </view>

      <view v-if="item.extra" class="extra-box">
        {{ item.extra }}
      </view>

      <view class="message-actions">
        <button
          v-if="item.url"
          class="action-btn primary"
          @click="go(item.url)"
        >
          去处理
        </button>

        <button class="action-btn ghost" @click="copyMessage(item)">
          复制内容
        </button>
      </view>
    </view>

    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getAccountState } from '@/utils/accountMock.js'
import { formatMoney } from '@/utils/moneyMock.js'
import { getDeviceTitle, getNowText } from '@/utils/tradeFlow.js'

const RECHARGE_KEY = 'recyclerRechargeApplyList'

const currentUser = ref({})
const inquiryList = ref([])
const rechargeApplyList = ref([])
const platformMessageList = ref([])
const accountState = ref(getAccountState())
const activeTab = ref('all')

onShow(() => {
  currentUser.value = uni.getStorageSync('currentUser') || {}

  if (!currentUser.value.role) {
    uni.reLaunch({
      url: '/pages/login/login'
    })
    return
  }

  loadData()
})

const messageList = computed(() => {
  const list = []

  list.push(...buildStoragePlatformMessages())
  list.push(...buildAccountMessages())
  list.push(...buildRechargeMessages())
  list.push(...buildTradeMessages())
  list.push(...buildCancelMessages())

  return list.sort((a, b) => {
    return getTimeValue(b.time) - getTimeValue(a.time)
  })
})

const unreadCount = computed(() => {
  return messageList.value.filter(item => item.important).length
})

const todayCount = computed(() => {
  const today = getTodayDateText()

  return messageList.value.filter(item => {
    return String(item.time || '').startsWith(today)
  }).length
})

const tabs = computed(() => {
  const auditCount = messageList.value.filter(item => item.type === 'audit').length
  const orderCount = messageList.value.filter(item => item.type === 'order').length
  const fundCount = messageList.value.filter(item => item.type === 'fund').length

  return [
    { key: 'all', name: '全部', badge: messageList.value.length },
    { key: 'audit', name: '审核', badge: auditCount },
    { key: 'order', name: '订单', badge: orderCount },
    { key: 'fund', name: '资金', badge: fundCount }
  ]
})

const currentMessages = computed(() => {
  if (activeTab.value === 'all') {
    return messageList.value
  }

  return messageList.value.filter(item => item.type === activeTab.value)
})

function loadData() {
  const list = uni.getStorageSync('inquiryList') || []

  inquiryList.value = list.map(item => {
    return {
      ...item,
      quotes: Array.isArray(item.quotes) ? item.quotes : []
    }
  })

  rechargeApplyList.value = uni.getStorageSync(RECHARGE_KEY) || []
  platformMessageList.value = uni.getStorageSync('platform_messages') || []
  accountState.value = getAccountState()
}

function buildStoragePlatformMessages() {
  if (currentUser.value.role !== 'platform_admin') {
    return []
  }

  return platformMessageList.value.map(item => {
    return {
      id: `platform_storage_${item.id}`,
      type: item.type || 'fund',
      icon: item.icon || '通',
      colorClass: item.colorClass || 'green',
      tag: item.tag || '系统消息',
      tagClass: item.tagClass || 'success',
      title: item.title || '平台消息',
      content: item.content || '',
      extra: item.extra || (item.orderNo ? `订单号：${item.orderNo}` : ''),
      time: item.time || '',
      important: Boolean(item.important),
      url: item.url || ''
    }
  })
}

function buildAccountMessages() {
  const user = currentUser.value
  const list = []

  if (user.status === 'pending') {
    list.push({
      id: `account_pending_${user.id}`,
      type: 'audit',
      icon: '审',
      colorClass: 'orange',
      tag: '待审核',
      tagClass: 'waiting',
      title: '账号正在等待审核',
      content: '你的账号申请已提交，请等待对应审核人或平台管理员审核。',
      extra: `当前身份：${roleText(user.role)}；公司：${user.company_name || '-'}`,
      time: user.created_at || '',
      important: true,
      url: ''
    })
  }

  if (user.status === 'approved') {
    list.push({
      id: `account_approved_${user.id}`,
      type: 'audit',
      icon: '通',
      colorClass: 'green',
      tag: '已通过',
      tagClass: 'success',
      title: '账号审核已通过',
      content: '你的账号已通过审核，可以正常使用对应身份的功能。',
      extra: `当前身份：${roleText(user.role)}；公司：${user.company_name || '-'}`,
      time: user.approved_at || user.created_at || '',
      important: false,
      url: '/pages/home/home'
    })
  }

  if (user.status === 'rejected') {
    list.push({
      id: `account_rejected_${user.id}`,
      type: 'audit',
      icon: '驳',
      colorClass: 'red',
      tag: '已驳回',
      tagClass: 'danger',
      title: '账号审核被驳回',
      content: '你的账号申请被驳回，请根据驳回原因重新提交或联系管理员。',
      extra: `驳回原因：${user.reject_reason || '-'}`,
      time: user.rejected_at || user.created_at || '',
      important: true,
      url: '/pages/login/login'
    })
  }

  if (user.role === 'platform_admin') {
    const pendingAccounts = (accountState.value.accounts || []).filter(item => item.status === 'pending')

    if (pendingAccounts.length > 0) {
      list.push({
        id: 'platform_account_pending',
        type: 'audit',
        icon: '审',
        colorClass: 'cyan',
        tag: '待处理',
        tagClass: 'waiting',
        title: '有新的账号申请待审核',
        content: `当前有 ${pendingAccounts.length} 个账号等待平台审核，请及时处理。`,
        extra: '包含商家老板、回收商老板、员工或库管账号。',
        time: getNowText(),
        important: true,
        url: '/pages/platform/payment/payment'
      })
    }
  }

  return list
}

function buildRechargeMessages() {
  const user = currentUser.value
  const list = []

  if (isRecyclerRole(user.role)) {
    const myApplyList = rechargeApplyList.value.filter(item => {
      return Number(item.companyId) === Number(user.company_id)
    })

    myApplyList.forEach(item => {
      if (item.status === 'pending') {
        list.push({
          id: `recharge_pending_${item.id}`,
          type: 'fund',
          icon: '款',
          colorClass: 'orange',
          tag: '待审核',
          tagClass: 'waiting',
          title: '充值申请已提交',
          content: `你提交的资金池充值申请 ¥${formatMoney(item.amount)} 正在等待平台审核。`,
          extra: `提交时间：${item.createTime || '-'}`,
          time: item.createTime || '',
          important: true,
          url: '/pages/recycler/settlement/settlement'
        })
      }

      if (item.status === 'approved') {
        list.push({
          id: `recharge_approved_${item.id}`,
          type: 'fund',
          icon: '通',
          colorClass: 'green',
          tag: '已入账',
          tagClass: 'success',
          title: '资金池充值审核通过',
          content: `平台已审核通过充值申请，¥${formatMoney(item.amount)} 已加入资金池。`,
          extra: `审核时间：${item.reviewTime || '-'}`,
          time: item.reviewTime || item.createTime || '',
          important: false,
          url: '/pages/recycler/settlement/settlement'
        })
      }

      if (item.status === 'rejected') {
        list.push({
          id: `recharge_rejected_${item.id}`,
          type: 'fund',
          icon: '驳',
          colorClass: 'red',
          tag: '已驳回',
          tagClass: 'danger',
          title: '资金池充值申请被驳回',
          content: `你提交的充值申请 ¥${formatMoney(item.amount)} 被平台驳回。`,
          extra: `驳回原因：${item.rejectReason || '-'}`,
          time: item.reviewTime || item.createTime || '',
          important: true,
          url: '/pages/recycler/settlement/settlement'
        })
      }
    })
  }

  if (user.role === 'platform_admin') {
    const pendingList = rechargeApplyList.value.filter(item => item.status === 'pending')

    if (pendingList.length > 0) {
      list.push({
        id: 'platform_recharge_pending',
        type: 'fund',
        icon: '款',
        colorClass: 'purple',
        tag: '待审核',
        tagClass: 'waiting',
        title: '有新的资金池充值申请',
        content: `当前有 ${pendingList.length} 条充值申请等待审核。`,
        extra: '审核通过后，充值金额会进入回收商资金池。',
        time: getNowText(),
        important: true,
        url: '/pages/platform/payment/payment'
      })
    }
  }

  return list
}

function buildTradeMessages() {
  const user = currentUser.value
  const list = []

  inquiryList.value.forEach(item => {
    if (isMerchantRelated(item, user)) {
      buildMerchantTradeMessages(list, item)
    }

    if (isRecyclerRelated(item, user)) {
      buildRecyclerTradeMessages(list, item)
    }

    if (user.role === 'platform_admin') {
      buildPlatformTradeMessages(list, item)
    }
  })

  return list
}

function buildMerchantTradeMessages(list, item) {
  const quoteCount = getQuoteList(item).length

  if (!item.tradeStatus && quoteCount > 0 && !isFinishedInquiry(item)) {
    list.push({
      id: `merchant_quote_${item.id}`,
      type: 'order',
      icon: '报',
      colorClass: 'blue',
      tag: '新报价',
      tagClass: 'processing',
      title: '你的询价收到回收商报价',
      content: `${getDeviceTitle(item)} 已收到 ${quoteCount} 家回收商报价，请及时查看并选择是否卖出。`,
      extra: `询价单号：${item.no || item.id}`,
      time: item.createTime || '',
      important: true,
      url: '/pages/merchant/inquiry/inquiry'
    })
  }

  if (item.tradeStatus === 'waiting_merchant_ship') {
    list.push({
      id: `merchant_ship_${item.id}`,
      type: 'order',
      icon: '寄',
      colorClass: 'orange',
      tag: '待发货',
      tagClass: 'waiting',
      title: '请寄出设备并上传快递单号',
      content: `${getDeviceTitle(item)} 已成交，请尽快发货并填写快递信息。`,
      extra: `成交时间：${item.dealTime || '-'}`,
      time: item.dealTime || '',
      important: true,
      url: '/pages/merchant/order/order'
    })
  }

  if (item.tradeStatus === 'merchant_shipped') {
    list.push({
      id: `merchant_shipped_${item.id}`,
      type: 'order',
      icon: '发',
      colorClass: 'blue',
      tag: '已发货',
      tagClass: 'processing',
      title: '设备已发货，等待回收商收货',
      content: `${getDeviceTitle(item)} 已上传快递单号，等待回收商收到快递并验货确认。`,
      extra: `快递：${item.expressCompany || '-'} ${item.expressNo || '-'}`,
      time: item.merchantShipTime || '',
      important: false,
      url: '/pages/merchant/order/order'
    })
  }

  if (item.tradeStatus === 'recycler_received') {
    list.push({
      id: `merchant_wait_platform_pay_${item.id}`,
      type: 'order',
      icon: '款',
      colorClass: 'purple',
      tag: '待打款',
      tagClass: 'processing',
      title: '回收商已确认收货，等待平台打款',
      content: `${getDeviceTitle(item)} 已由回收商确认收货，平台管理员将给商家打款。`,
      extra: `确认收货时间：${item.recyclerReceiveTime || '-'}`,
      time: item.recyclerReceiveTime || '',
      important: true,
      url: '/pages/merchant/order/order'
    })
  }

  if (item.tradeStatus === 'platform_paid') {
    list.push({
      id: `merchant_paid_${item.id}`,
      type: 'order',
      icon: '成',
      colorClass: 'green',
      tag: '已完成',
      tagClass: 'success',
      title: '平台已打款，交易完成',
      content: `${getDeviceTitle(item)} 的交易已完成，请核对收款情况。`,
      extra: `平台打款时间：${item.platformPayTime || '-'}`,
      time: item.platformPayTime || '',
      important: false,
      url: '/pages/merchant/order/order'
    })
  }
}

function buildRecyclerTradeMessages(list, item) {
  const myQuote = getMyQuote(item)

  if (!myQuote) return

  if (!item.tradeStatus) {
    list.push({
      id: `recycler_quoted_${item.id}`,
      type: 'order',
      icon: '报',
      colorClass: 'blue',
      tag: '已报价',
      tagClass: 'processing',
      title: '你已提交报价',
      content: `${getDeviceTitle(item)} 已提交报价 ¥${myQuote.amount}，等待商家选择。`,
      extra: '回收商之间无法查看彼此报价。',
      time: myQuote.updateTime || myQuote.quoteTime || '',
      important: false,
      url: '/pages/recycler/inquiry/inquiry'
    })
  }

  if (isAcceptedByOther(item)) {
    list.push({
      id: `recycler_lost_${item.id}`,
      type: 'order',
      icon: '结',
      colorClass: 'gray',
      tag: '已结束',
      tagClass: 'gray',
      title: '询价已被其他回收商完成',
      content: `${getDeviceTitle(item)} 已由其他回收商成交，你不能继续报价。`,
      extra: `成交时间：${item.dealTime || '-'}`,
      time: item.dealTime || '',
      important: false,
      url: '/pages/recycler/order/order'
    })
  }

  if (isAcceptedByMe(item) && item.tradeStatus === 'waiting_merchant_ship') {
    list.push({
      id: `recycler_wait_ship_${item.id}`,
      type: 'order',
      icon: '等',
      colorClass: 'blue',
      tag: '待发货',
      tagClass: 'processing',
      title: '商家已确认成交，等待发货',
      content: `${getDeviceTitle(item)} 已成交，当前等待商家寄出设备。`,
      extra: `成交时间：${item.dealTime || '-'}`,
      time: item.dealTime || '',
      important: false,
      url: '/pages/recycler/order/order'
    })
  }

  if (isAcceptedByMe(item) && item.tradeStatus === 'merchant_shipped') {
    list.push({
      id: `recycler_receive_${item.id}`,
      type: 'order',
      icon: '收',
      colorClass: 'orange',
      tag: '待收货',
      tagClass: 'waiting',
      title: '商家已发货，请收货验机',
      content: `${getDeviceTitle(item)} 已发货。收到快递后请先录制开箱视频，再确认收货。`,
      extra: `快递：${item.expressCompany || '-'} ${item.expressNo || '-'}`,
      time: item.merchantShipTime || '',
      important: true,
      url: '/pages/recycler/order/order'
    })
  }

  if (isAcceptedByMe(item) && item.tradeStatus === 'recycler_received') {
    list.push({
      id: `recycler_received_${item.id}`,
      type: 'order',
      icon: '验',
      colorClass: 'green',
      tag: '已收货',
      tagClass: 'success',
      title: '已确认收货，等待平台打款给商家',
      content: `${getDeviceTitle(item)} 已确认收货，平台管理员会进行打款处理。`,
      extra: `确认时间：${item.recyclerReceiveTime || '-'}`,
      time: item.recyclerReceiveTime || '',
      important: false,
      url: '/pages/recycler/order/order'
    })
  }

  if (isAcceptedByMe(item) && item.tradeStatus === 'platform_paid') {
    list.push({
      id: `recycler_done_${item.id}`,
      type: 'order',
      icon: '成',
      colorClass: 'green',
      tag: '完成',
      tagClass: 'success',
      title: '交易已完成',
      content: `${getDeviceTitle(item)} 的交易已由平台确认打款完成。`,
      extra: `完成时间：${item.platformPayTime || '-'}`,
      time: item.platformPayTime || '',
      important: false,
      url: '/pages/recycler/order/order'
    })
  }
}

function buildPlatformTradeMessages(list, item) {
  if (item.paymentStatus === 'pending' || item.tradeStatus === 'payment_reviewing') {
    list.push({
      id: `platform_payment_${item.id}`,
      type: 'audit',
      icon: '付',
      colorClass: 'purple',
      tag: '付款审核',
      tagClass: 'waiting',
      title: '有付款截图等待审核',
      content: `${item.selectedRecyclerCompanyName || '回收商'} 已提交 ${getDeviceTitle(item)} 的付款截图，请审核。`,
      extra: `付款金额：¥${item.paymentAmount || '-'}`,
      time: item.paymentSubmitTime || '',
      important: true,
      url: '/pages/platform/payment/payment'
    })
  }

  if (item.tradeStatus === 'recycler_received') {
    list.push({
      id: `platform_pay_merchant_${item.id}`,
      type: 'fund',
      icon: '款',
      colorClass: 'orange',
      tag: '待打款',
      tagClass: 'waiting',
      title: '回收商已确认收货，请给商家打款',
      content: `${getDeviceTitle(item)} 已由回收商确认收货，请平台管理员向商家打款。`,
      extra: `商家：${item.merchantCompanyName || item.company_name || '-'}；金额：¥${item.selectedAmount || '-'}`,
      time: item.recyclerReceiveTime || '',
      important: true,
      url: '/pages/platform/payment/payment'
    })
  }
}

function buildCancelMessages() {
  const user = currentUser.value
  const list = []

  inquiryList.value.forEach(item => {
    if (item.cancelApplyStatus === 'pending' && user.role === 'platform_admin') {
      list.push({
        id: `cancel_pending_platform_${item.id}`,
        type: 'audit',
        icon: '取',
        colorClass: 'red',
        tag: '取消审核',
        tagClass: 'waiting',
        title: '有取消订单申请等待审核',
        content: `${item.cancelApplyUserName || '用户'} 申请取消 ${getDeviceTitle(item)} 的订单，请审核。`,
        extra: `取消原因：${item.cancelApplyReason || '-'}`,
        time: item.cancelApplyTime || '',
        important: true,
        url: '/pages/platform/payment/payment'
      })
    }

    const isRelated = isMerchantRelated(item, user) || isRecyclerRelated(item, user)
    if (!isRelated) return

    if (item.cancelApplyStatus === 'pending') {
      list.push({
        id: `cancel_pending_user_${item.id}`,
        type: 'audit',
        icon: '取',
        colorClass: 'orange',
        tag: '审核中',
        tagClass: 'waiting',
        title: '取消订单申请已提交',
        content: `${getDeviceTitle(item)} 的取消申请正在等待平台管理员审核。`,
        extra: `申请原因：${item.cancelApplyReason || '-'}`,
        time: item.cancelApplyTime || '',
        important: true,
        url: isMerchantRole(user.role) ? '/pages/merchant/order/order' : '/pages/recycler/order/order'
      })
    }

    if (item.cancelApplyStatus === 'approved') {
      list.push({
        id: `cancel_approved_${item.id}`,
        type: 'audit',
        icon: '通',
        colorClass: 'green',
        tag: '已取消',
        tagClass: 'success',
        title: '取消订单申请已通过',
        content: `${getDeviceTitle(item)} 的订单已由平台管理员审核取消。`,
        extra: `审核时间：${item.cancelReviewTime || '-'}`,
        time: item.cancelReviewTime || item.cancelApplyTime || '',
        important: false,
        url: isMerchantRole(user.role) ? '/pages/merchant/order/order' : '/pages/recycler/order/order'
      })
    }

    if (item.cancelApplyStatus === 'rejected') {
      list.push({
        id: `cancel_rejected_${item.id}`,
        type: 'audit',
        icon: '驳',
        colorClass: 'red',
        tag: '已驳回',
        tagClass: 'danger',
        title: '取消订单申请被驳回',
        content: `${getDeviceTitle(item)} 的取消订单申请被平台管理员驳回，订单继续进行。`,
        extra: `驳回原因：${item.cancelRejectReason || '-'}`,
        time: item.cancelReviewTime || item.cancelApplyTime || '',
        important: true,
        url: isMerchantRole(user.role) ? '/pages/merchant/order/order' : '/pages/recycler/order/order'
      })
    }
  })

  return list
}

function isMerchantRelated(item, user) {
  if (user.role === 'merchant_owner') {
    return Number(item.merchantCompanyId) === Number(user.company_id) ||
      Number(item.company_id) === Number(user.company_id)
  }

  if (user.role === 'merchant_staff') {
    return Number(item.merchantUserId) === Number(user.id) ||
      Number(item.merchant_id) === Number(user.id)
  }

  return false
}

function isRecyclerRelated(item, user) {
  if (!isRecyclerRole(user.role)) return false

  if (Number(item.selectedRecyclerCompanyId) === Number(user.company_id)) {
    return true
  }

  return !!getMyQuote(item)
}

function getQuoteList(item) {
  return Array.isArray(item.quotes) ? item.quotes : []
}

function getMyQuote(item) {
  return getQuoteList(item).find(quote => {
    return Number(quote.recyclerCompanyId) === Number(currentUser.value.company_id)
  })
}

function isAcceptedByMe(item) {
  return (item.status === '商家已接单' || item.quoteStatus === 'accepted') &&
    Number(item.selectedRecyclerCompanyId) === Number(currentUser.value.company_id)
}

function isAcceptedByOther(item) {
  return (item.status === '商家已接单' || item.quoteStatus === 'accepted') &&
    item.selectedRecyclerCompanyId &&
    Number(item.selectedRecyclerCompanyId) !== Number(currentUser.value.company_id)
}

function isFinishedInquiry(item) {
  return item.status === '商家已接单' ||
    item.status === '商家已下架' ||
    item.status === '交易完成' ||
    item.status === '订单已取消' ||
    item.quoteStatus === 'accepted' ||
    item.quoteStatus === 'off_shelf' ||
    item.quoteStatus === 'done' ||
    item.quoteStatus === 'cancelled'
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

function isRecyclerRole(role) {
  return role === 'recycler_owner' ||
    role === 'recycler_keeper' ||
    role === 'recycler_staff'
}

function isMerchantRole(role) {
  return role === 'merchant_owner' ||
    role === 'merchant_staff'
}

function go(url) {
  if (!url) return

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

function goHome() {
  uni.reLaunch({
    url: '/pages/home/home'
  })
}

function refreshPage() {
  loadData()

  uni.showToast({
    title: '已刷新',
    icon: 'success'
  })
}

function copyMessage(item) {
  const text = `${item.title}\n${item.content}\n${item.extra || ''}`

  uni.setClipboardData({
    data: text,
    success() {
      uni.showToast({
        title: '已复制',
        icon: 'success'
      })
    }
  })
}

function getTimeValue(time) {
  if (!time) return 0

  const value = new Date(String(time).replace(/-/g, '/')).getTime()

  return Number.isNaN(value) ? 0 : value
}

function getTodayDateText() {
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')

  return `${yyyy}-${mm}-${dd}`
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
  margin: 0 24rpx 22rpx;
  padding: 8rpx;
  border-radius: 999rpx;
  background: #ffffff;
  box-shadow: none;
}

.tab {
  position: relative;
  flex: 1;
  height: 72rpx;
  line-height: 72rpx;
  text-align: center;
  border-radius: 999rpx;
  color: #64748b;
  font-size: 26rpx;
  font-weight: bold;
}

.tab.active {
  background: #17324d;
  color: #ffffff;
}

.tab-badge {
  position: absolute;
  right: 6rpx;
  top: -8rpx;
  min-width: 32rpx;
  height: 32rpx;
  line-height: 32rpx;
  border-radius: 999rpx;
  background: #ff5a3c;
  color: #ffffff;
  font-size: 24rpx;
}

.tool-row {
  display: flex;
  gap: 18rpx;
  margin: 0 24rpx 24rpx;
}

.tool-btn {
  flex: 1;
  height: 72rpx;
  line-height: 72rpx;
  text-align: center;
  border-radius: 999rpx;
  background: #17324d;
  color: #ffffff;
  font-size: 26rpx;
  font-weight: bold;
}

.tool-btn.light {
  background: #ffffff;
  color: #374151;
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

.message-card {
  margin: 0 24rpx 24rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
  border: 2rpx solid transparent;
}

.message-card.important {
  border-color: rgba(75, 85, 99, 0.35);
}

.message-head {
  display: flex;
  align-items: flex-start;
}

.message-icon {
  width: 76rpx;
  height: 76rpx;
  margin-right: 20rpx;
  border-radius: 24rpx;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 600;
}

.message-icon.orange {
  background: #ff8a48;
}

.message-icon.blue {
  background: #2f80ed;
}

.message-icon.green {
  background: #18a058;
}

.message-icon.red {
  background: #ff5a3c;
}

.message-icon.purple {
  background: #17324d;
}

.message-icon.cyan {
  background: #17324d;
}

.message-icon.gray {
  background: #9ca3af;
}

.message-main {
  flex: 1;
}

.message-title {
  color: #111111;
  font-size: 30rpx;
  font-weight: 600;
  line-height: 40rpx;
}

.message-time {
  margin-top: 8rpx;
  color: #999999;
  font-size: 24rpx;
}

.message-tag {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
  font-weight: bold;
  white-space: nowrap;
}

.message-tag.waiting {
  background: #fff7e6;
  color: #d97706;
}

.message-tag.processing {
  background: #eef0f4;
  color: #374151;
}

.message-tag.success {
  background: #ecfdf3;
  color: #18a058;
}

.message-tag.danger {
  background: #fff0eb;
  color: #ff5a3c;
}

.message-tag.gray {
  background: #eef2f7;
  color: #667085;
}

.message-content {
  margin-top: 22rpx;
  color: #555555;
  font-size: 26rpx;
  line-height: 42rpx;
}

.extra-box {
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #f6f7f9;
  color: #667085;
  font-size: 24rpx;
  line-height: 36rpx;
}

.message-actions {
  display: flex;
  gap: 18rpx;
  margin-top: 24rpx;
}

.action-btn {
  flex: 1;
  height: 76rpx;
  line-height: 76rpx;
  border-radius: 999rpx;
  font-size: 27rpx;
  font-weight: bold;
}

.action-btn::after {
  border: none;
}

.action-btn.primary {
  background: #17324d;
  color: #ffffff;
}

.action-btn.ghost {
  background: #f1f5f9;
  color: #667085;
}

.safe-bottom {
  height: 60rpx;
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
