import { get, post, put, del } from './request.js'

// ================= 系统通用 API =================
export const devAPI = {
  init: () => post('/dev/init')
}

// 通用上传接口 (注意：这里在前端实际调用时，可能需要使用 uni.uploadFile 而不是封装的 request)
// 需求文档提及：上传营业执照、设备图片、线下付款凭证等
export const commonAPI = {
  uploadImage: (filePath) => post('/upload/image', { filePath }), 
}

// ================= 用户与认证 API =================
export const authAPI = {
  // 微信一键登录+手机号绑定
  wechatLogin: (data) => post('/auth/wechat', data),
}

export const userAPI = {
  getUsers: () => get('/users'),
  getUser: (id) => get(`/users/${id}`)
}

// ================= 商家端 API (Merchant) =================
export const merchantAPI = {
  // 商家入驻资料提交 (包含营业执照、联系人信息等)
  createCompany: (data) => post('/merchant/company', data),
  getCompanyStaff: (companyId) => get(`/merchant/company/${companyId}/staff`),
  updateStaffPermissions: (staffId, data) => put(`/merchant/staff/${staffId}/permissions`, data),
  // 提交线下汇款保证金凭证
  submitDepositProof: (data) => post('/merchant/deposit/proof', data)
}

// 设备信息发布与管理
export const deviceAPI = {
  // 商家发布设备信息（支持草稿、上下架）
  publishDevice: (data) => post('/devices', data),
  // 获取设备列表
  getDeviceList: (params) => get('/devices', params),
  // 更新设备信息
  updateDevice: (id, data) => put(`/devices/${id}`, data)
}

// 商家询价管理
export const inquiryAPI = {
  // 对单个设备向一个或多个回收商发起询价
  createInquiry: (data) => post('/inquiries', data),
  getInquiries: (userId) => get('/inquiries', { user_id: userId }),
  getInquiryDetail: (id) => get(`/inquiries/${id}`)
}

// ================= 回收商端 API (Recycler) =================
export const recyclerAPI = {
  getCompanies: () => get('/recycler/companies'),
  // 维护基础资料与结算账户
  updateAccount: (data) => put('/recycler/account', data)
}

// 报价处理
export const quoteAPI = {
  // 快速填写报价及有效期、备注
  createQuote: (data) => post('/quotes', data),
  getQuotes: (inquiryId) => get('/quotes', { inquiry_id: inquiryId }),
  // 商家接受报价
  acceptQuote: (data) => post('/quotes/accept', data),
  // 回收商拒单
  rejectQuote: (id, data) => post(`/quotes/${id}/reject`, data)
}

// ================= 订单与物流 API (核心流转) =================
export const orderAPI = {
  // 商家填写发货信息、上传快递单号
  submitLogistics: (orderId, data) => post(`/orders/${orderId}/logistics`, data),
  // 查看物流节点
  getLogisticsInfo: (orderId) => get(`/orders/${orderId}/logistics`),
  // 回收商验机结果录入 (通过/调价/退货)
  submitInspection: (orderId, data) => post(`/orders/${orderId}/inspection`, data),
  // 商家确认或申诉验机结果
  confirmInspection: (orderId, data) => post(`/orders/${orderId}/confirm`, data)
}

// ================= 资金结算 API =================
export const financeAPI = {
  // 查看待结算订单与应付金额
  getSettlements: (params) => get('/finance/settlements', params),
  // 提交线下付款凭证
  submitPaymentProof: (data) => post('/finance/payment/proof', data)
}

// ================= 消息与客服 API =================
export const messageAPI = {
  // 获取节点通知 (订单、报价、资金相关)
  getMessages: (params) => get('/messages', params),
  // 标记已读
  markAsRead: (id) => put(`/messages/${id}/read`)
}