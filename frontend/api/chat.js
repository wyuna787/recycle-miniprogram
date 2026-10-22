// api/chat.js
import request from '@/utils/request.js'

export default {
  // 获取聊天列表
  getChatList() {
    return request({
      url: '/chat/list',
      method: 'GET'
    })
  },

  // 获取聊天消息历史
  getChatMessages(userId, page = 1, size = 20) {
    return request({
      url: `/chat/messages?userId=${userId}&page=${page}&size=${size}`,
      method: 'GET'
    })
  },

  // 标记消息为已读
  markAsRead(userId) {
    return request({
      url: `/chat/read/${userId}`,
      method: 'POST'
    })
  },

  // 获取在线用户数量
  getOnlineCount() {
    return request({
      url: '/chat/online-count',
      method: 'GET'
    })
  },

  // 检查用户在线状态
  checkUserOnline(userId) {
    return request({
      url: `/chat/online-status/${userId}`,
      method: 'GET'
    })
  },

  // 发送消息（HTTP方式，作为WebSocket的备用）
  sendMessage(data) {
    return request({
      url: '/chat/send',
      method: 'POST',
      data
    })
  }
}