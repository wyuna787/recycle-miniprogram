// api/product.js
import request from '@/utils/request.js'

export default {
  // 获取商品详情
  getProductDetail(productId) {
    return request({
      url: `/product/detail/${productId}`,
      method: 'GET'
    })
  },

  // 获取商品列表
  getProductList(params = {}) {
    return request({
      url: '/product/list',
      method: 'GET',
      data: params
    })
  },

  // 收藏商品
  collectProduct(productId) {
    return request({
      url: '/product/collect',
      method: 'POST',
      data: { productId }
    })
  },

  // 取消收藏
  uncollectProduct(productId) {
    return request({
      url: '/product/uncollect',
      method: 'POST',
      data: { productId }
    })
  },

  // 检查收藏状态
  checkCollectStatus(productId) {
    return request({
      url: `/product/collect/status/${productId}`,
      method: 'GET'
    })
  }
}
