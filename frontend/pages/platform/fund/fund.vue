<template>
  <view class="page">
    <custom-navbar title="资金池管理" />

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">平台管理员</view>
          <view class="title">资金池管理</view>
          <view class="desc">
            直接设置各回收商的资金池余额。本系统不涉及真实现金，仅做额度数字管理。
          </view>
        </view>

        <view class="hero-icon">池</view>
      </view>

      <view class="sum-card">
        <view class="sum-item">
          <view class="sum-num">{{ fundRows.length }}</view>
          <view class="sum-label">回收商数</view>
        </view>
        <view class="sum-item">
          <view class="sum-num">¥{{ formatMoney(totalBalance) }}</view>
          <view class="sum-label">总余额</view>
        </view>
        <view class="sum-item">
          <view class="sum-num">¥{{ formatMoney(totalFrozen) }}</view>
          <view class="sum-label">冻结中</view>
        </view>
      </view>
    </view>

    <view class="company-card">
      <view>回收商 {{ fundRows.length }} 家 · 商家 {{ depositRows.length }} 家</view>
      <view class="tabs"><text @click="companyKind='recycler'">回收商</text>　<text @click="companyKind='merchant'">商家</text></view>
      <input class="edit-input" v-model="companySearch" placeholder="公司ID / 公司名称" />
    </view>
    <view v-if="companyKind==='recycler' && visibleFunds.length === 0" class="empty">
      暂无回收商账户
    </view>

    <view
      v-for="row in visibleFunds"
      :key="row.companyId"
      class="company-card"
    >
      <view class="company-head">
        <view>
          <view class="company-name">{{ row.companyName }}</view>
          <view class="company-id">公司ID：{{ row.companyId }}</view>
        </view>

        <view class="avail-tag">可用 ¥{{ formatMoney(row.balance - row.frozenAmount) }}</view>
      </view>

      <view class="readonly-row">
        <view class="ro-cell">
          <text class="ro-label">冻结中</text>
          <text class="ro-value">¥{{ formatMoney(row.frozenAmount) }}</text>
        </view>
        <view class="ro-cell">
          <text class="ro-label">已扣款</text>
          <text class="ro-value">¥{{ formatMoney(row.deductedAmount) }}</text>
        </view>
      </view>

      <view class="edit-row">
        <view class="edit-label">资金池总余额</view>
        <input
          class="edit-input"
          type="digit"
          v-model="row.editBalance"
          placeholder="请输入余额"
        />
      </view>

      <input class="edit-input" type="digit" v-model="row.changeAmount" placeholder="充值或扣除金额" />
      <button :disabled="adjusting" @click="adjust(row,'recycler','recharge')">充值</button>
      <button :disabled="adjusting" @click="adjust(row,'recycler','deduct')">扣除</button>
      <button class="save-btn" @click="saveBalance(row)">
        保存余额
      </button>
    </view>

    <view class="company-card" v-for="row in visibleDeposits" :key="'deposit-'+row.id">
      <view class="company-name">{{ row.company_name }} · 商家</view>
      <view class="company-id">公司ID：{{ row.id }} · 当前额度 ¥{{ formatMoney(row.deposit_amount) }}</view>
      <view class="company-id">公司注册时间：{{ row.registered_at || '未记录' }} · {{ row.status==='active'?'正常使用':'已停用' }}</view>
      <view>{{ row.settlement_mode==='ship'?'保证金额度内发货即到款':'确认收货后到款' }}</view>
      <view v-if="row.deposit_overdue" style="color:#c0392b">注册已满一个月未缴纳保证金，请安排业务员跟进（不会自动停用）。</view>
      <view v-if="row.pending_application">
        <view>待核实保证金 ¥{{ formatMoney(row.pending_application.amount) }} · {{ row.pending_application.created_at }}</view>
        <view>{{ row.pending_application.remark }}</view>
        <button :disabled="adjusting" @click="reviewDeposit(row,'approve')">核实到账并确认</button>
        <button :disabled="adjusting" @click="reviewDeposit(row,'reject')">驳回申请</button>
      </view>
      <textarea class="edit-input" v-model="row.followup" placeholder="登记业务员、跟进情况及处理结果（仅管理员可见）" />
      <view v-if="row.followup_time">最近跟进：{{ row.followup_by }} · {{ row.followup_time }}</view>
      <button :disabled="adjusting" @click="saveFollowup(row)">保存跟进记录</button>
      <input class="edit-input" type="digit" v-model="row.changeAmount" placeholder="充值或退款金额" />
      <button :disabled="adjusting" @click="adjust(row,'merchant','recharge')">充值金额</button>
      <button :disabled="adjusting" @click="adjust(row,'merchant','refund')">退款金额</button>
      <view class="company-id">保证金额度内，确认发货即可到账；签收后释放占用额度。</view>
      <input class="edit-input" type="digit" v-model="row.editAmount" placeholder="请输入已核实保证金额度" />
      <button class="save-btn" @click="saveDeposit(row)">保存保证金额度</button>
    </view>
    <view class="safe-bottom"></view>
  </view>
</template>

<script setup>
import { get, post } from '@/utils/request.js'
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { formatMoney } from '@/utils/moneyMock.js'
import { getNowText } from '@/utils/tradeFlow.js'
import { getAccountState } from '@/utils/accountMock.js'
import { guardPage } from '@/utils/permission.js'
import { getAdminFundPools, setFundBalance, getMerchantDeposits, setMerchantDeposit } from '@/api/fund.js'

async function reviewDeposit(row,action){
 uni.showModal({title:action==='approve'?'确认实际到账':'驳回申请',content:action==='approve'?'确认已收到保证金 ¥'+formatMoney(row.pending_application.amount)+'？确认后全公司新成交订单按保证金模式结算。':'确认驳回本次保证金申请？',editable:true,placeholderText:'核实凭据或处理备注',success:async res=>{
  if(!res.confirm||adjusting.value)return
  adjusting.value=true
  try{await post('/api/admin/merchant/deposit-applies/'+row.pending_application.id+'/review',{action,remark:res.content||''});await loadData();uni.showToast({title:'已处理',icon:'success'})}catch(e){}finally{adjusting.value=false}
 }})
}
async function saveFollowup(row){
 if(adjusting.value)return
 adjusting.value=true
 try{await post('/api/admin/merchant/'+row.id+'/deposit-followup',{note:row.followup||''});await loadData();uni.showToast({title:'已保存',icon:'success'})}catch(e){}finally{adjusting.value=false}
}
const FUND_KEY = 'recyclerFundPoolList'

const currentUser = ref({})
const fundRows = ref([])
const depositRows = ref([])
const companyKind=ref('recycler'),companySearch=ref(''),adjusting=ref(false)
const matches=(id,name)=>!companySearch.value.trim() || String(id)===companySearch.value.trim() || String(name).toLowerCase().includes(companySearch.value.trim().toLowerCase())
const visibleFunds=computed(()=>companyKind.value==='recycler'?fundRows.value.filter(r=>matches(r.companyId,r.companyName)):[])
const visibleDeposits=computed(()=>companyKind.value==='merchant'?depositRows.value.filter(r=>matches(r.id,r.company_name)):[])
async function adjust(row,kind,action){
 const amount=Number(row.changeAmount)
 if(!Number.isFinite(amount)||amount<=0)return uni.showToast({title:'请输入有效金额',icon:'none'})
 uni.showModal({title:action==='recharge'?'确认充值':action==='refund'?'确认退款':'确认扣除',content:'手工登记额度 ¥'+formatMoney(amount),success:async result=>{
  if(!result.confirm||adjusting.value)return
  adjusting.value=true
  try{await post('/api/admin/balance/adjust',{company_type:kind,company_id:row.companyId||row.id,action,amount,request_id:Date.now().toString(36)+'-'+Math.random().toString(36).slice(2)});await loadData();uni.showToast({title:'已登记',icon:'success'})}catch(e){}finally{adjusting.value=false}
 }})
}

onShow(() => {
  currentUser.value = uni.getStorageSync('currentUser') || uni.getStorageSync('userInfo') || {}

  if (!guardPage(currentUser.value, '/pages/platform/fund/fund')) return

  loadData()
})

const totalBalance = computed(() => {
  return fundRows.value.reduce((sum, item) => sum + Number(item.balance || 0), 0)
})

const totalFrozen = computed(() => {
  return fundRows.value.reduce((sum, item) => sum + Number(item.frozenAmount || 0), 0)
})

async function loadData() {
  try {
    const deposits = await getMerchantDeposits()
    depositRows.value = (deposits.list || []).map(row => ({ ...row, editAmount: String(row.deposit_amount || 0) }))
    const res = await getAdminFundPools()
    fundRows.value = (res.list || []).map(item => {
      const balance = Number(item.balance || 0)
      return {
        companyId: Number(item.company_id),
        companyName: item.company_name || `回收商${item.company_id}`,
        balance,
        frozenAmount: Number(item.frozen_amount || 0),
        deductedAmount: Number(item.deducted_amount || 0),
        editBalance: String(balance)
      }
    })
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  const funds = uni.getStorageSync(FUND_KEY) || []
  const fundMap = {}
  funds.forEach(item => { fundMap[Number(item.companyId)] = item })

  // 从账号体系里取所有回收商公司（去重），合并已有资金池数据
  const accounts = (getAccountState().accounts || []).filter(item => item.company_type === 'recycler')
  const companyMap = {}

  accounts.forEach(acc => {
    const id = Number(acc.company_id)
    if (!id || companyMap[id]) return
    companyMap[id] = acc.company_name || `回收商${id}`
  })

  // 已有资金池但账号列表里没有的公司也要展示
  funds.forEach(item => {
    const id = Number(item.companyId)
    if (!companyMap[id]) companyMap[id] = item.companyName || `回收商${id}`
  })

  fundRows.value = Object.keys(companyMap).map(idStr => {
    const id = Number(idStr)
    const fund = fundMap[id] || {}
    const balance = Number(fund.balance || 0)

    return {
      companyId: id,
      companyName: companyMap[id],
      balance,
      frozenAmount: Number(fund.frozenAmount || 0),
      deductedAmount: Number(fund.deductedAmount || 0),
      editBalance: String(balance)
    }
  })
}

async function saveBalance(row) {
  const newBalance = Number(row.editBalance)

  if (Number.isNaN(newBalance) || newBalance < 0) {
    uni.showToast({ title: '请输入正确的余额', icon: 'none' })
    return
  }

  if (newBalance < row.frozenAmount) {
    uni.showModal({
      title: '余额低于冻结金额',
      content: `该回收商当前已冻结 ¥${formatMoney(row.frozenAmount)}，总余额不能低于冻结金额。`,
      showCancel: false
    })
    return
  }

  try {
    const info = await setFundBalance(row.companyId, newBalance)
    row.balance = Number(info.balance != null ? info.balance : newBalance)
    row.frozenAmount = Number(info.frozen_amount || row.frozenAmount || 0)
    row.deductedAmount = Number(info.deducted_amount || row.deductedAmount || 0)
    uni.showToast({ title: '已保存', icon: 'success' })
    return
  } catch (error) {
    return // 请求失败不得恢复历史模拟数据
  }

  const funds = uni.getStorageSync(FUND_KEY) || []
  let fund = funds.find(item => Number(item.companyId) === row.companyId)

  if (!fund) {
    fund = {
      companyId: row.companyId,
      companyName: row.companyName,
      balance: 0,
      frozenAmount: 0,
      deductedAmount: 0
    }
    funds.unshift(fund)
  }

  fund.balance = newBalance
  fund.companyName = row.companyName
  fund.updatedTime = getNowText()

  uni.setStorageSync(FUND_KEY, funds)

  row.balance = newBalance

  uni.showToast({ title: '已保存', icon: 'success' })
}
async function saveDeposit(row) {
  const amount = Number(row.editAmount)
  if (!Number.isFinite(amount) || amount < 0) return uni.showToast({ title: '请输入有效额度', icon: 'none' })
  try { await setMerchantDeposit(row.id, amount); uni.showToast({ title: '已保存', icon: 'success' }) } catch(e) { /* request displays error */ }
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

.sum-card {
  display: flex;
  margin-top: 30rpx;
  gap: 16rpx;
}

.sum-item {
  flex: 1;
  padding: 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.2);
  text-align: center;
}

.sum-num {
  font-size: 34rpx;
  font-weight: 600;
}

.sum-label {
  margin-top: 6rpx;
  font-size: 24rpx;
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

.company-card {
  margin: 0 24rpx 24rpx;
  padding: 30rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.company-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.company-name {
  color: #111111;
  font-size: 32rpx;
  font-weight: 600;
}

.company-id {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.avail-tag {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #ecfdf3;
  color: #18a058;
  font-size: 24rpx;
  font-weight: bold;
}

.readonly-row {
  display: flex;
  gap: 16rpx;
  margin-top: 22rpx;
}

.ro-cell {
  flex: 1;
  display: flex;
  justify-content: space-between;
  padding: 18rpx;
  border-radius: 18rpx;
  background: #f6f7f9;
  font-size: 24rpx;
}

.ro-label {
  color: #64748b;
}

.ro-value {
  color: #222222;
  font-weight: bold;
}

.edit-row {
  margin-top: 24rpx;
}

.edit-label {
  margin-bottom: 12rpx;
  color: #333333;
  font-size: 26rpx;
  font-weight: bold;
}

.edit-input {
  height: 88rpx;
  padding: 0 24rpx;
  border-radius: 22rpx;
  background: #f5f8fb;
  font-size: 32rpx;
  box-sizing: border-box;
}

.save-btn {
  margin-top: 22rpx;
  height: 82rpx;
  line-height: 82rpx;
  border-radius: 999rpx;
  background: #17324d;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: bold;
}

.save-btn::after {
  border: none;
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
