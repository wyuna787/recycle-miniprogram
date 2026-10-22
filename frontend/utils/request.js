// 本地开发：http://127.0.0.1:8000（本机启动 uvicorn 后端时使用）
// 远程部署：http://127.0.0.1:8000（后端代码部署到该服务器后切换回这一行）
// 微信开发者工具如无法访问，请改为电脑局域网 IP，例如 http://192.168.x.x:8000
// 正式上线必须改为 HTTPS 域名，例如 https://api.xxx.com
import { expireAccountSession } from './session.js'

const BASE_URL = 'http://127.0.0.1:8000'

function getErrorMessage(data) {
  if (!data) {
    return '请求失败'
  }

  const detail = data.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (detail && typeof detail === 'object' && detail.message) {
    return detail.message
  }

  return data.message || '请求失败'
}

function request(options = {}) {
  const token = uni.getStorageSync('token')
  const header = {
    'Content-Type': 'application/json',
    ...(options.header || {})
  }

  if (token) {
    header.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      timeout: options.timeout || 15000,
      header,
      success: (res) => {
        if (token !== uni.getStorageSync('token')) {
          reject({ message: '账号已切换', staleSession: true })
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }

        if (res.statusCode === 401 || res.data?.detail?.code === 'ACCOUNT_DISABLED') {
          if (token) expireAccountSession(token)

          const errorData = {
            statusCode: res.statusCode,
            ...(res.data || {}),
            message: res.data?.detail?.message || '登录已失效，请重新登录'
          }

          if (options.showError !== false) {
            uni.showToast({
              title: errorData.message,
              icon: 'none',
              duration: 2500
            })
          }

          reject(errorData)
          return
        }

        const errorData = {
          statusCode: res.statusCode,
          ...(res.data || {}),
          message: getErrorMessage(res.data)
        }

        if (options.showError !== false) {
          uni.showToast({
            title: errorData.message,
            icon: 'none',
            duration: 2500
          })
        }

        reject(errorData)
      },
      fail: (error) => {
        if (options.showError !== false) {
          uni.showToast({
            title: '后端连接失败',
            icon: 'none'
          })
        }

        reject(error)
      }
    })
  })
}

export default request

/**
 * 上传图片到后端 /upload/image，返回可访问的完整图片 URL。
 * 上传失败时 reject，调用方可回退到本地临时路径以保证预览不中断。
 */
export function uploadImage(filePath, options = {}) {
  const token = uni.getStorageSync('token')
  const header = {}

  if (token) {
    header.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + (options.url || '/upload/image'),
      filePath,
      name: options.name || 'file',
      header,
      success: (res) => {
        if (token !== uni.getStorageSync('token')) { reject({ staleSession: true }); return }
        let responseData = res.data
        try { responseData = JSON.parse(res.data) } catch (e) {}
        if (res.statusCode === 401 || responseData?.detail?.code === 'ACCOUNT_DISABLED') {
          if (token) expireAccountSession(token)
          reject(res)
          return
        }
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(res)
          return
        }

        let data = res.data

        if (typeof data === 'string') {
          try {
            data = JSON.parse(data)
          } catch (e) {
            data = {}
          }
        }

        const rel = (data && (data.url || data.path)) || ''

        if (!rel) {
          reject(new Error('上传返回为空'))
          return
        }

        resolve(rel.indexOf('http') === 0 ? rel : BASE_URL + rel)
      },
      fail: reject
    })
  })
}

export const get = (url, data, options = {}) => {
  return request({
    url,
    method: 'GET',
    data,
    ...options
  })
}

export const post = (url, data, options = {}) => {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  })
}

export const put = (url, data, options = {}) => {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  })
}

export const del = (url, data, options = {}) => {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options
  })
}

export { BASE_URL }
