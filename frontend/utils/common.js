// 通用工具函数

/**
 * 格式化价格
 */
export const formatPrice = (price) => {
	if (price == null || price === undefined) return '¥0.00'
	return `¥${Number(price).toFixed(2)}`
}

/**
 * 格式化时间
 */
export const formatTime = (timestamp) => {
	if (!timestamp) return ''
	
	const now = Date.now()
	const diff = now - new Date(timestamp).getTime()
	
	const minute = 60 * 1000
	const hour = 60 * minute
	const day = 24 * hour
	const month = 30 * day
	
	if (diff < minute) {
		return '刚刚'
	} else if (diff < hour) {
		return `${Math.floor(diff / minute)}分钟前`
	} else if (diff < day) {
		return `${Math.floor(diff / hour)}小时前`
	} else if (diff < month) {
		return `${Math.floor(diff / day)}天前`
	} else {
		const date = new Date(timestamp)
		return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
	}
}

/**
 * 显示Toast消息
 */
export const showToast = (title, icon = 'none') => {
	uni.showToast({
		title,
		icon,
		duration: 2000
	})
}

/**
 * 显示确认对话框
 */
export const showConfirm = (title, content = '') => {
	return new Promise((resolve) => {
		uni.showModal({
			title,
			content,
			success: (res) => {
				resolve(res.confirm)
			}
		})
	})
}

/**
 * 选择图片
 */
export const chooseImage = (count = 1) => {
	return new Promise((resolve, reject) => {
		uni.chooseImage({
			count,
			sizeType: ['compressed'],
			sourceType: ['album', 'camera'],
			success: (res) => {
				resolve(res.tempFilePaths)
			},
			fail: reject
		})
	})
}

/**
 * 压缩图片
 */
export const compressImage = (src, quality = 0.8) => {
	return new Promise((resolve, reject) => {
		uni.compressImage({
			src,
			quality,
			success: (res) => {
				resolve(res.tempFilePath)
			},
			fail: reject
		})
	})
}

/**
 * 获取用户位置
 */
export const getLocation = () => {
	return new Promise((resolve, reject) => {
		uni.getLocation({
			type: 'gcj02',
			success: resolve,
			fail: reject
		})
	})
}

/**
 * 预览图片
 */
export const previewImage = (urls, current = 0) => {
	uni.previewImage({
		urls,
		current: typeof current === 'number' ? urls[current] : current
	})
}

/**
 * 复制到剪贴板
 */
export const copyText = (text) => {
	return new Promise((resolve, reject) => {
		uni.setClipboardData({
			data: text,
			success: () => {
				showToast('复制成功')
				resolve()
			},
			fail: reject
		})
	})
}

/**
 * 拨打电话
 */
export const makePhoneCall = (phoneNumber) => {
	uni.makePhoneCall({
		phoneNumber
	})
}

/**
 * 微信登录
 */
export const wxLogin = () => {
	return new Promise((resolve, reject) => {
		// #ifdef MP-WEIXIN
		uni.login({
			provider: 'weixin',
			success: (res) => {
				if (res.code) {
					resolve(res.code)
				} else {
					reject(new Error('获取微信登录code失败'))
				}
			},
			fail: reject
		})
		// #endif
		
		// #ifndef MP-WEIXIN
		uni.showToast({
			title: '请在微信小程序中使用',
			icon: 'none'
		})
		reject(new Error('请在微信小程序中使用'))
		// #endif
	})
}

/**
 * 获取微信用户信息 - 已废弃，改为使用button的open-type
 */
export const getWxUserProfile = () => {
	return new Promise((resolve, reject) => {
		// #ifdef MP-WEIXIN
		// 这个方法已经被废弃，现在使用button的open-type="getUserProfile"
		uni.showToast({
			title: '请使用微信登录按钮',
			icon: 'none'
		})
		reject(new Error('getUserProfile已被废弃，请使用button的open-type'))
		// #endif
		
		// #ifndef MP-WEIXIN
		reject(new Error('请在微信小程序中使用'))
		// #endif
	})
}

/**
 * 防抖函数
 */
export const debounce = (func, wait) => {
	let timeout
	return function executedFunction(...args) {
		const later = () => {
			clearTimeout(timeout)
			func.apply(this, args)
		}
		clearTimeout(timeout)
		timeout = setTimeout(later, wait)
	}
}

/**
 * 检查是否已登录
 */
export const checkLogin = () => {
	const token = uni.getStorageSync('token')
	return !!token
}

/**
 * 获取用户信息
 */
export const getUserInfo = () => {
	return uni.getStorageSync('userInfo')
}

/**
 * 跳转到登录页面
 */
export const goToLogin = () => {
	uni.navigateTo({
		url: '/pages/login/login'
	})
}

/**
 * 检查登录状态，未登录则跳转到登录页
 */
export const requireLogin = () => {
	if (!checkLogin()) {
		uni.showToast({
			title: '请先登录',
			icon: 'none'
		})
		setTimeout(() => {
			goToLogin()
		}, 1500)
		return false
	}
	return true
}

/**
 * 获取系统信息 - 使用新API
 */
export const getSystemInfo = () => {
	// #ifdef MP-WEIXIN
	try {
		// 使用新的API获取系统信息
		const systemInfo = {
			...wx.getAppBaseInfo(),
			...wx.getDeviceInfo(),
			...wx.getWindowInfo()
		}
		return systemInfo
	} catch (error) {
		console.warn('获取系统信息失败，使用兼容方式:', error)
		// 兼容旧版本
		return wx.getSystemInfoSync()
	}
	// #endif
	
	// #ifndef MP-WEIXIN
	return uni.getSystemInfoSync()
	// #endif
}

/**
 * 获取状态栏高度
 */
export const getStatusBarHeight = () => {
	try {
		const systemInfo = getSystemInfo()
		return systemInfo.statusBarHeight || 0
	} catch (error) {
		console.warn('获取状态栏高度失败:', error)
		return 0
	}
}