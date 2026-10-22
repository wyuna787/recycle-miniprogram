<template>
  <view class="board">
    <custom-navbar :title="title" :intercept-back="!!selected" @back="selectedId = null" />
    <view v-if="selected" class="detail">
      <button class="back" @click="selectedId = null">‹ 返回列表</button>
      <view class="panel">
        <view class="heading">{{ getDeviceTitle(selected) }}</view>
        <view :class="['state',selected.status==='confirmed'?'red':'']">{{ statusLabel(selected) }}</view>
        <view v-if="isInquiry" class="muted">{{ remainingText(selected) }}</view>
        <view v-else class="price">成交金额 ¥{{ customerView ? String(Math.floor(Number(selected.merchantDisplayAmount || 0))) : formatMoney(selected.price) }}</view>
        <view v-if="!isRecycler && !isInquiry && !customerView">我的收益 ¥{{ formatMoney(selected.myCommission) }}（{{ ((selected.myCommissionRate || 0)*100).toFixed(2) }}%）</view>
        <view v-if="!isInquiry && selected.quote?.remark" class="muted quote-remark">报价备注：{{ selected.quote.remark }}</view>
        <view v-if="!isInquiry && !customerView" class="muted">{{ selected.fund_status==='deducted'?'已到账 / 已扣款':'待到账 / 资金已冻结' }}</view>
      </view>
      <view v-if="!isInquiry && !isRecycler" class="panel">
        <view class="heading">回收商收货信息</view>
        <view>{{ selected.recycler?.company_name || '回收商' }}</view>
        <view @click="copyText(selected.recycler?.contact_name)">{{ selected.recycler?.contact_name || '收件人未填写' }}</view>
        <view @click="copyText(selected.recycler?.contact_phone)">{{ selected.recycler?.contact_phone || '电话未填写' }}</view>
        <view @click="copyText(selected.recycler?.address)">{{ selected.recycler?.address || '地址未填写，请联系回收商补充' }}</view>
      </view>
      <device-report :item="selected" />
      <view v-if="isInquiry && !isRecycler" class="panel">
        <view class="heading">最高报价</view>
        <view v-if="!selected.quotes?.length" class="muted">暂无报价</view>
        <view v-for="(quote,index) in displayedQuotes" :key="quote.id" class="quote">
          <view>{{ quote.recyclerCompanyName || '回收商' }}</view>
          <view class="price">成交金额 ¥{{ customerView ? String(Math.floor(Number(quote.merchantDisplayAmount || 0))) : formatMoney(quote.price) }}</view>
          <view v-if="!customerView">我的收益 ¥{{ formatMoney(quote.myCommission) }}</view>
          <view v-if="quote.remark" class="muted quote-remark">报价备注：{{ quote.remark }}</view>
          <button v-if="!isTraded(selected)" :disabled="busy" @click="accept(selected,quote)">同意卖出</button>
        </view>
      </view>
      <view v-if="isInquiry && isRecycler" class="panel">
        <view v-if="myQuote(selected)" class="price">我的报价 ¥{{ formatMoney(myQuote(selected).price) }}</view>
        <view v-if="canQuote(selected)">
          <input class="input" type="digit" v-model="quoteAmount" placeholder="请输入完整报价金额" />
          <textarea class="input" v-model="quoteRemark" placeholder="报价备注（可选）" />
          <button :disabled="busy" @click="submitQuote">{{ myQuote(selected) ? '修改报价' : '提交报价' }}</button>
        </view>
        <view v-else class="muted">{{ isTraded(selected)?'商家已确认成交，不能继续报价':'报价时间已结束' }}</view>
      </view>
      <view v-if="!isInquiry && !isRecycler && selected.status==='confirmed'" class="panel">
        <view class="heading">填写发货信息</view>
        <input class="input" v-model="expressCompany" placeholder="快递公司" />
        <input class="input" v-model="trackingNo" placeholder="快递单号" />
        <button :disabled="busy" @click="chooseProof">上传发货凭证（必填）</button>
        <view class="muted">已上传 {{ shipImages.length }} 张凭证</view>
        <button :disabled="busy" @click="ship">确认已发货</button>
      </view>
      <view v-if="!isInquiry && isRecycler && ['recycler_owner','recycler_keeper'].includes(user.role) && selected.status==='shipped'" class="panel">
        <view class="muted">签收前请核对设备并留存开箱视频。</view>
        <button :disabled="busy" @click="receive">确认签收</button>
      </view>
      <view v-if="!isInquiry" class="panel">
        <view class="heading">订单操作</view>
        <view v-if="selected.cancel_apply_status==='pending'" class="muted">取消审核中</view>
        <button v-if="!isRecycler && ['confirmed','shipped'].includes(selected.status) && selected.cancel_apply_status!=='pending'" :disabled="busy" @click="requestCancel">申请取消订单</button>
        <button v-if="!isRecycler && ['confirmed','shipped','received','inspection_done'].includes(selected.status)" :disabled="busy" @click="requestAppeal">联系平台申诉</button>
        <button v-if="isRecycler && selected.status==='received'" :disabled="busy" @click="inspection">提交验机结果</button>
        <button v-if="!isRecycler && selected.status==='inspection_done'" :disabled="busy" @click="confirmInspection">确认验机结果</button>
        <view v-if="selected.shipping_images?.length" class="muted" @click="previewProof">查看发货凭证（{{ selected.shipping_images.length }}张）</view>
        <view v-if="selected.inspection_reason">验机备注：{{ selected.inspection_reason }}</view>
        <view v-if="selected.appeal_reason">申诉：{{ selected.appeal_reason }}</view>
      </view>
    </view>
    <view v-else>
      <view class="search-row"><image src="/static/business/search.svg" mode="aspectFit" /><input class="search" v-model="search" placeholder="订单号 / 询价单号 / 型号" confirm-type="search" /><text v-if="search" @click="search=''">清除</text></view>
      <view class="tabs"><view v-for="tab in tabs" :key="tab.key" :class="['tab',activeTab===tab.key?'active':'']" @click="activeTab=tab.key">{{ tab.label }}</view></view>
      <view v-if="error" class="error">{{ error }} <text @click="reload">点击重试</text></view>
      <view v-if="loading && !items.length" class="muted">加载中…</view>
      <view v-if="!loading && !visibleItems.length && !error" class="empty">{{ search ? '未找到匹配订单' : '暂无订单' }}</view>
      <view v-for="item in visibleItems" :key="item.key" class="compact" @click="open(item)">
        <view class="merchant">{{ item.merchantCompanyName || item.merchant?.company_name || user.company_name || '商家' }} <text :class="['state',item.status==='confirmed'?'red':'']">{{ statusLabel(item) }}</text></view>
        <view class="compact-row">
          <image v-if="thumbnail(item)" :src="thumbnail(item)" mode="aspectFill" />
          <view v-else class="placeholder">机</view>
          <view class="summary"><view class="heading">{{ getDeviceTitle(item) }}</view><view>{{ item.condition || item.device?.condition || '-' }} · {{ item.storage || item.device?.storage || '-' }}</view><view class="muted">{{ item.order_no || item.no || `XJ${item.id}` }}</view><view v-if="item.kind==='inquiry'" class="muted">{{ remainingText(item) }}</view></view>
          <view v-if="item.kind==='inquiry' && isRecycler" class="entry">{{ myQuote(item) ? '¥' + formatMoney(myQuote(item).price) : (canQuote(item) ? '抢单 ›' : '') }}</view>
          <view v-else class="entry">查看 ›</view>
        </view>
        <view v-if="!isRecycler && item.kind==='inquiry' && item.quotes?.length" class="price">最高成交价 ¥{{ displayAmount(item.quotes[0]) }}</view>
        <view v-if="!isRecycler && item.kind==='order'" class="price">成交价 ¥{{ displayAmount(item) }}</view>
      </view>
      <button :disabled="loading" @click="reload">刷新</button>
    </view>
  </view>
</template>
<script setup>
import { ref, computed, onUnmounted } from 'vue'
import DeviceReport from './device-report.vue'
import { getMyInquiries,getRecyclerInquiries,getMyQuotes,getMyOrders,createQuote,acceptQuote,shipOrder,receiveOrder,inspectOrder,confirmOrder,appealOrder } from '@/api/trade.js'
import { getDeviceTitle,getTradeFlowStatusLabel } from '@/utils/tradeFlow.js'
import { cancelApplyOrder } from '@/api/fund.js'
import { uploadImage } from '@/utils/request.js'
import { formatMoney } from '@/utils/moneyMock.js'
const props=defineProps({mode:{type:String,required:true},customerView:{type:Boolean,default:false}})
const customerView=computed(()=>props.customerView)
function displayAmount(item){return customerView.value ? String(Math.floor(Number(item.merchantDisplayAmount ?? 0))) : formatMoney(item.price)}
const displayedQuotes=computed(()=>{const quotes=selected.value?.quotes || [];return quotes.slice(0,1)})
const user=ref({}),items=ref([]),selectedId=ref(null),activeTab=ref('waiting'),search=ref(''),busy=ref(false),loading=ref(false),error=ref(''),now=ref(Date.now())
const shipImages=ref([])
const quoteAmount=ref(''),quoteRemark=ref(''),expressCompany=ref(''),trackingNo=ref('')
let refreshTimer=null,tickTimer=null,epoch=0
const isRecycler=computed(()=>props.mode.startsWith('recycler'))
const inquiryOnly=computed(()=>props.mode.endsWith('inquiry'))
const title=computed(()=>inquiryOnly.value ? (isRecycler.value?'收到的询价':'我的询价') : (isRecycler.value?'回收订单':'订单管理'))
const selected=computed(()=>items.value.find(item=>item.key===selectedId.value))
const isInquiry=computed(()=>selected.value?.kind==='inquiry')
const tabs=computed(()=>inquiryOnly.value?[{key:'waiting',label:'待报价'},{key:'quoted',label:'已报价'},{key:'finished',label:'已结束'}]:[{key:'waiting',label:isRecycler.value?'待发货':'待报价'},...(isRecycler.value?[{key:'shipping',label:'待收货'},{key:'receiving',label:'已完成'},{key:'finished',label:'全部'}]:[{key:'finished',label:'已结束'},{key:'shipping',label:'待发货'},{key:'receiving',label:'待收货'}])])
const isTraded=item=>['confirmed','shipped','received','completed','inspection_done','appealing','closed','cancelled','accepted'].includes(item.status)
const deadline=item=>new Date(String(item.quote_deadline || '').replace(/-/g,'/')).getTime()
const ended=item=>isTraded(item)||item.can_quote===false||!Number.isFinite(deadline(item))||now.value>=deadline(item)
const myQuote=item=>item.quotes?.find(q=>Number(q.quoteUserId || q.recycler_id)===Number(user.value.id)) || (user.value.role==='recycler_owner'?item.quotes?.[0]:null)
const canQuote=item=>item.kind==='inquiry'&&!ended(item)&&['recycler_owner','recycler_staff'].includes(user.value.role)
function remainingText(item){if(isTraded(item))return '已成交';if(ended(item))return '报价已结束';const seconds=Math.max(0,Math.ceil((deadline(item)-now.value)/1000));return `剩余 ${Math.floor(seconds/60)}分${seconds%60}秒`}
function statusLabel(item){if(item.kind==='inquiry'&&!isTraded(item)){if(ended(item))return '已结束';if(isRecycler.value)return myQuote(item)?'已报价':'待报价';return item.quotes?.length?'已报价':'待报价'}return getTradeFlowStatusLabel(item.status)}
const visibleItems=computed(()=>items.value.filter(item=>{
 const term=search.value.trim().toLowerCase();if(term && ![item.order_no,item.no,`XJ${item.inquiry_id || item.id}`,item.id,getDeviceTitle(item),item.merchantCompanyName,item.merchant?.company_name].some(v=>String(v || '').toLowerCase().includes(term)))return false
 if(term)return true
 if(inquiryOnly.value){if(activeTab.value==='finished')return ended(item);if(ended(item))return false;const quoted=isRecycler.value?!!myQuote(item):!!item.quotes?.length;return activeTab.value==='quoted'?quoted:!quoted}
 if(isRecycler.value){if(activeTab.value==='finished')return true;if(activeTab.value==='waiting')return item.status==='confirmed';if(activeTab.value==='shipping')return ['shipped','received'].includes(item.status);return ['completed','closed','cancelled','inspection_done'].includes(item.status)}
 if(activeTab.value==='waiting')return item.kind==='inquiry'&&!ended(item);if(item.kind==='inquiry')return activeTab.value==='finished'&&ended(item);if(item.kind!=='order')return false;if(activeTab.value==='shipping')return item.status==='confirmed';if(activeTab.value==='receiving')return ['shipped','received','inspection_done','appealing'].includes(item.status);return ['completed','closed','cancelled'].includes(item.status)
}))
function copyText(value){if(value)uni.setClipboardData({data:String(value)})}
function thumbnail(item){return item.images?.[0] || item.device?.images?.[0] || ''}
function open(item){selectedId.value=item.key;quoteAmount.value=myQuote(item)?String(myQuote(item).price):'';quoteRemark.value=myQuote(item)?.remark || '';shipImages.value=item.shipping_images || [];expressCompany.value=item.express_company||'';trackingNo.value=item.tracking_no||'';uni.pageScrollTo({scrollTop:0,duration:0})}
function stop(){epoch++;clearInterval(refreshTimer);clearInterval(tickTimer);refreshTimer=tickTimer=null}
async function reload(){
 if(loading.value)return
 const current=uni.getStorageSync('userInfo') || uni.getStorageSync('currentUser') || {}
 if(user.value.id!==current.id){items.value=[];selectedId.value=null}
 user.value=current
 if(!current.id){uni.reLaunch({url:'/pages/login/login'});return}
 loading.value=true;error.value='';const stamp=epoch
 try{
  const ordersRes=await getMyOrders()
  const orders=(ordersRes.list||[]).map(o=>({...o,kind:'order',key:`order:${o.id}`,merchantCompanyName:o.merchant?.company_name,...o.device}))
  let inquiries=[]
  if(inquiryOnly.value || !isRecycler.value){
   const res=isRecycler.value?await getRecyclerInquiries():await getMyInquiries()
   if(isRecycler.value){const qr=await getMyQuotes();inquiries=(res.list||[]).map(o=>({...o,quotes:(qr.list||[]).filter(q=>q.inquiry_id===o.id)}))}
   else {inquiries=(res.list||[]).map(o=>({...o,quotes:(o.quotes||[]).sort((a,b)=>Number(b.price)-Number(a.price)).slice(0,5)}))}
   const ordered=new Set(orders.map(o=>o.inquiry_id))
   if(!inquiryOnly.value)inquiries=inquiries.filter(o=>!ordered.has(o.id))
   inquiries=inquiries.map(o=>({...o,kind:'inquiry',key:`inquiry:${o.id}`}))
  }
  if(stamp!==epoch)return
  items.value=inquiryOnly.value?inquiries:[...inquiries,...orders]
 }catch(e){if(stamp===epoch){items.value=[];error.value=e.message||'加载失败，请重试'}}finally{loading.value=false}
}
function start(){stop();reload();refreshTimer=setInterval(reload,5000);tickTimer=setInterval(()=>{now.value=Date.now()},1000)}
async function mutate(fn){if(busy.value)return;busy.value=true;try{await fn();uni.showToast({title:'操作成功',icon:'success'});await reload()}catch(e){/* request displays the server error */}finally{busy.value=false}}
async function submitQuote(){const amount=Number(quoteAmount.value);if(!selected.value || !canQuote(selected.value))return uni.showToast({title:'报价已结束',icon:'none'});if(!Number.isFinite(amount)||amount<=0)return uni.showToast({title:'请输入有效报价',icon:'none'});const id=selected.value.id;await mutate(()=>createQuote({inquiry_id:id,price:amount,remark:quoteRemark.value,valid_days:1}))}
function accept(item,quote){uni.showModal({title:'确认成交',content:`按成交金额 ¥${displayAmount(quote)} 卖出？确认后生成交易订单。`,success:res=>{if(res.confirm)mutate(async()=>{await acceptQuote(quote.id);selectedId.value=null;if(!inquiryOnly.value)activeTab.value='shipping'})}})}
function ship(){if(!shipImages.value.length)return uni.showToast({title:'请上传发货凭证',icon:'none'});if(!expressCompany.value.trim()||!trackingNo.value.trim())return uni.showToast({title:'请填写快递公司和单号',icon:'none'});const id=selected.value.id;mutate(()=>shipOrder(id,{express_company:expressCompany.value.trim(),tracking_no:trackingNo.value.trim(),shipping_images:shipImages.value}))}
function previewProof(){uni.previewImage({urls:selected.value.shipping_images})}
function receive(){const id=selected.value.id;uni.showModal({title:'确认签收',content:'确认已收到该订单设备？签收后完成结算。',success:res=>{if(res.confirm)mutate(async()=>{await receiveOrder(id);selectedId.value=null;activeTab.value='shipping'})}})}
async function chooseProof(){
  uni.chooseImage({count:3,success:async res=>{
    busy.value=true
    try { const urls=await Promise.all(res.tempFilePaths.map(path=>uploadImage(path)));shipImages.value=[...shipImages.value,...urls] }
    catch(e){uni.showToast({title:'上传失败，请重试',icon:'none'})}finally{busy.value=false}
  }})
}
function requestCancel(){const id=selected.value.id;uni.showModal({title:'申请取消',editable:true,placeholderText:'请填写取消原因',success:res=>{if(res.confirm&&res.content?.trim())mutate(()=>cancelApplyOrder(id,res.content.trim()))}})}
function requestAppeal(){const id=selected.value.id;uni.showModal({title:'提交申诉',editable:true,placeholderText:'请填写申诉原因',success:res=>{if(res.confirm&&res.content?.trim())mutate(()=>appealOrder(id,{appeal_reason:res.content.trim()}))}})}
function inspection(){const id=selected.value.id;uni.showActionSheet({itemList:['验机通过','验机调价','验机退货'],success:res=>{
 const type=['pass','adjust','reject'][res.tapIndex]
 if(type==='pass')return mutate(()=>inspectOrder(id,{inspection_type:'pass'}))
 uni.showModal({title:type==='adjust'?'输入调价金额':'输入退货原因',editable:true,success:result=>{
  if(!result.confirm)return
  if(type==='adjust'){const price=Number(result.content);if(!Number.isFinite(price)||price<=0)return uni.showToast({title:'金额无效',icon:'none'});mutate(()=>inspectOrder(id,{inspection_type:type,inspection_price:price}))}
  else if(result.content?.trim())mutate(()=>inspectOrder(id,{inspection_type:type,inspection_reason:result.content.trim()}))
 }})
}})}
function confirmInspection(){const id=selected.value.id;uni.showModal({title:'确认验机',content:'确认验机结果并结束订单？',success:res=>{if(res.confirm)mutate(()=>confirmOrder(id))}})}
onUnmounted(stop)
defineExpose({start,stop,reload})
</script>




<style scoped>

.board{min-height:100vh;background:#f3f5f7;padding:24rpx;box-sizing:border-box}.search,.input{background:#fff;padding:24rpx;margin:16rpx 0;border-radius:16rpx;font-size:28rpx}.tabs{display:flex;background:#fff;padding:8rpx;border-radius: 16rpx;margin-bottom:20rpx}.tab{flex:1;text-align:center;padding:20rpx 6rpx;font-size:26rpx;color:#777}.active{background:#344054;color:#fff;border-radius: 16rpx}.compact,.panel{background:#fff;border-radius:24rpx;padding:24rpx;margin:16rpx 0}.merchant{display:flex;justify-content:space-between;font-size:24rpx;color:#777;margin-bottom:16rpx;gap:16rpx}.compact-row{display:flex;gap:20rpx;align-items:center}.compact-row image,.placeholder{width:112rpx;height:112rpx;border-radius:16rpx;flex-shrink:0}.placeholder{display:flex;align-items:center;justify-content:center;background:#edf1f5;font-size:40rpx}.summary{flex:1;min-width:0;font-size:24rpx;color:#666}.heading{font-size:30rpx;font-weight:bold;color:#222;margin-bottom:12rpx}.entry{color:#2979ff;white-space:nowrap;font-size:26rpx}.muted{font-size: 24rpx;color:#64748b;line-height:36rpx;overflow-wrap:anywhere}.state{color:#b97812;font-size: 24rpx}.red{color:#e54848;font-weight:bold}.price{font-size:30rpx;color:#f06840;margin-top:12rpx}.quote-remark{white-space:pre-wrap;overflow-wrap:anywhere}.quote{padding:20rpx 0;border-bottom:1rpx solid #eee}.board button{margin-top:20rpx;border-radius: 16rpx;background:#344054;color:#fff;font-size:28rpx}.board .back{background:#fff;color:#344054}.input{background:#f5f6f8}.error,.empty{padding:36rpx;text-align:center;color:#777}



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
