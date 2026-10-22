<template>
  <view class="page">
    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hello">欢迎使用</view>
          <view class="title">中晨回收</view>
        </view>

        <view class="mini-program-pill">
          <view class="phone-icon">▣</view>
          <text>小程序服务</text>
        </view>
      </view>

    </view>

    <view class="main-card">
      <view class="mode-tabs">
        <view
          :class="['mode-tab', mode === 'login' ? 'active' : '']"
          @click="switchMode('login')"
        >
          登录
        </view>

        <view
          :class="['mode-tab', mode === 'register' ? 'active' : '']"
          @click="switchMode('register')"
        >
          注册
        </view>
      </view>

      <!-- 登录 -->
      <view v-if="mode === 'login'">
        <view class="section-title">账号登录</view>
        <view class="section-desc">
          请输入手机号和密码。账号注册后，需平台管理员审核通过才能登录。
        </view>

        <view class="form-item">
          <view class="label">手机号</view>
          <input
            class="input"
            v-model="loginPhone"
            type="number"
            placeholder="请输入手机号"
          />
        </view>

        <view class="form-item">
          <view class="label">密码</view>
          <input
            class="input"
            v-model="loginPassword"
            type="password"
            placeholder="请输入密码"
          />
        </view>

        <view class="agreement-row">
          <view :class="['agree-box', agreed ? 'checked' : '']" @click="agreed = !agreed">
            <text v-if="agreed" class="agree-tick">✓</text>
          </view>
          <view class="agree-text">
            我已阅读并同意<text class="agree-link" @click.stop="openAgreement">《用户服务协议》</text>和<text class="agree-link" @click.stop="openPrivacy">《隐私政策》</text>
          </view>
        </view>

        <button class="primary-btn" @click="handleLogin">
          登录
        </button>

      </view>

      <!-- 注册 -->
      <view v-if="mode === 'register'">
        <view class="section-title">注册账号</view>
        <view class="section-desc">
          每个手机号只能注册一个身份账号。提交后等待平台管理员审核，通过后才可登录。
        </view>

        <view class="form-item">
          <view class="label">手机号</view>
          <input
            class="input"
            v-model="registerForm.phone"
            type="number"
            placeholder="请输入手机号"
          />
        </view>

        <view class="form-item">
          <view class="label">昵称 / 姓名</view>
          <input
            class="input"
            v-model="registerForm.nickname"
            placeholder="请输入昵称或姓名"
          />
        </view>

        <view class="form-item">
          <view class="label">设置密码</view>
          <input
            class="input"
            v-model="registerForm.password"
            type="password"
            placeholder="请设置登录密码"
          />
        </view>

        <view class="form-item">
          <view class="label">确认密码</view>
          <input
            class="input"
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入密码"
          />
        </view>

        <view class="form-item">
          <view class="label">申请身份</view>

          <view class="role-grid">
            <view
              v-for="item in roleOptions"
              :key="item.value"
              :class="['role-card', registerForm.role === item.value ? 'active' : '']"
              @click="chooseRole(item.value)"
            >
              <view class="role-icon">{{ item.icon }}</view>
              <view class="role-name">{{ item.label }}</view>
              <view class="role-desc">{{ item.desc }}</view>
            </view>
          </view>
        </view>

        <view v-if="needCompany" class="form-item">
          <view class="label">所属公司</view>

          <!-- 商家老板：可新建或加入公司；回收商老板只能加入已有 -->
          <view v-if="isOwnerRole">
            <view class="company-mode-tabs">
              <view :class="['company-mode-tab', companyMode==='new'?'active':'']" @click="companyMode='new'">新建公司</view>
              
            </view>
            <view v-if="companyMode==='new'" class="form-item" style="margin-top:8px">
              <input class="input" v-model="newCompanyName" placeholder="请输入公司名称" />
            </view>
            <view v-else>
              <picker :range="companyPickerNames" :value="companyPickerIndex" @change="handleCompanyChange">
                <view class="picker-box">
                  <text>{{ selectedCompanyName || '请选择所属公司' }}</text>
                  <text class="picker-arrow">⌄</text>
                </view>
              </picker>
            </view>
          </view>

          <!-- 员工/库管：只能加入已有公司 -->
          <view v-else>
            <picker :range="companyPickerNames" :value="companyPickerIndex" @change="handleCompanyChange">
              <view class="picker-box">
                <text>{{ selectedCompanyName || '请选择所属公司' }}</text>
                <text class="picker-arrow">⌄</text>
              </view>
            </picker>
          </view>
        </view>

        <view class="form-item">
          <view class="label">申请说明</view>
          <textarea
            class="textarea"
            v-model="registerForm.apply_reason"
            placeholder="请简单说明申请原因，例如：申请成为回收商A员工"
          />
        </view>

        <view class="agreement-row">
          <view :class="['agree-box', agreed ? 'checked' : '']" @click="agreed = !agreed">
            <text v-if="agreed" class="agree-tick">✓</text>
          </view>
          <view class="agree-text">
            我已阅读并同意<text class="agree-link" @click.stop="openAgreement">《用户服务协议》</text>和<text class="agree-link" @click.stop="openPrivacy">《隐私政策》</text>
          </view>
        </view>

        <button class="primary-btn" @click="handleRegister">
          提交注册申请
        </button>
      </view>
    </view>

    <view class="float-btn" @click="resetData">
      ↻
    </view>
  </view>
</template>

<script setup>
import { clearAccountSession } from '@/utils/session.js'
import { ref, computed, onMounted } from 'vue'
import {
  getAccountState,
  resetAccountState
} from '@/utils/accountMock.js'
import {
  getCompanies,
  register,
  login
} from '@/api/account.js'

const mode = ref('login')
const state = ref(getAccountState())
const loading = ref(false)

const loginPhone = ref('')
const loginPassword = ref('')

const agreed = ref(false)

function openAgreement() {
  uni.navigateTo({ url: '/pages/common/agreement/agreement' })
}
function openPrivacy() {
  uni.navigateTo({ url: '/pages/common/privacy/privacy' })
}

const confirmPassword = ref('')
const companyMode = ref('new')   // 老板注册时：new=新建公司 join=加入已有
const newCompanyName = ref('')   // 新建公司名称

const registerForm = ref({
  phone: '',
  nickname: '',
  password: '',
  role: '',
  company_type: '',
  company_id: '',
  apply_reason: ''
})

const isOwnerRole = computed(() => {
  return registerForm.value.role === 'merchant_owner' || registerForm.value.role === 'recycler_owner'
})

// 只有商家老板能「新建公司」；回收商老板只能加入已有公司
const isMerchantOwner = computed(() => registerForm.value.role === 'merchant_owner')

const roleOptions = [
  {
    label: '商家老板',
    value: 'merchant_owner',
    icon: '商',
    desc: '发布设备、管理订单和员工'
  },
  {
    label: '商家员工',
    value: 'merchant_staff',
    icon: '员',
    desc: '按老板授权发起询价'
  },
  {
    label: '回收商老板',
    value: 'recycler_owner',
    icon: '老',
    desc: '管理报价、资金和员工'
  },
  {
    label: '回收商库管',
    value: 'recycler_keeper',
    icon: '库',
    desc: '充值预付款、签收和查数据'
  },
  {
    label: '回收商员工',
    value: 'recycler_staff',
    icon: '抢',
    desc: '自行抢单、报价'
  },
  {
    label: '平台管理员',
    value: 'platform_admin',
    icon: '管',
    desc: '审核账号和权限'
  }
]

const needCompany = computed(() => {
  return registerForm.value.role &&
    registerForm.value.role !== 'platform_admin'
})

const currentCompanyType = computed(() => {
  if (registerForm.value.role.indexOf('merchant') === 0) {
    return 'merchant'
  }

  if (registerForm.value.role.indexOf('recycler') === 0) {
    return 'recycler'
  }

  return 'platform'
})

const currentCompanyList = computed(() => {
  if (currentCompanyType.value === 'merchant') {
    return state.value.merchantCompanies || []
  }

  if (currentCompanyType.value === 'recycler') {
    return state.value.recyclerCompanies || []
  }

  return []
})

const companyPickerNames = computed(() => {
  return currentCompanyList.value.map(item => `${item.name}（公司编号：${item.id}）`)
})

const companyPickerIndex = computed(() => {
  const index = currentCompanyList.value.findIndex(item => {
    return Number(item.id) === Number(registerForm.value.company_id)
  })

  return index >= 0 ? index : 0
})

const selectedCompanyName = computed(() => {
  const company = currentCompanyList.value.find(item => {
    return Number(item.id) === Number(registerForm.value.company_id)
  })

  if (!company) {
    return ''
  }

  return company.name
})

onMounted(() => {
  loadCompanies()
})

async function loadCompanies() {
  try {
    const res = await getCompanies()
    state.value = {
      ...getAccountState(),
      merchantCompanies: res.merchantCompanies || [],
      recyclerCompanies: res.recyclerCompanies || []
    }
  } catch (error) {
    state.value = getAccountState()
  }
}

function switchMode(type) {
  mode.value = type
}

async function handleLogin() {
  if (!agreed.value) {
    uni.showToast({
      title: '请先阅读并同意《用户服务协议》和《隐私政策》',
      icon: 'none'
    })
    return
  }

  if (!loginPhone.value) {
    uni.showToast({
      title: '请输入手机号',
      icon: 'none'
    })
    return
  }

  if (!loginPassword.value) {
    uni.showToast({
      title: '请输入密码',
      icon: 'none'
    })
    return
  }

  if (loading.value) {
    return
  }

  loading.value = true

  try {
    const res = await login({
      phone: loginPhone.value,
      password: loginPassword.value
    })

    if (res.status !== 'approved') {
      uni.showToast({
        title: '账号状态异常，请联系管理员',
        icon: 'none'
      })
      return
    }

    const user = res.userInfo || {}

    clearAccountSession()
    uni.setStorageSync('token', res.token)
    uni.setStorageSync('userInfo', user)
    uni.setStorageSync('currentUser', user)

    uni.showToast({
      title: '登录成功',
      icon: 'success'
    })

    setTimeout(() => {
      uni.reLaunch({
        url: '/pages/home/home'
      })
    }, 300)
  } catch (error) {
    const detail = error?.detail

    if (detail?.status === 'pending') {
      uni.showToast({
        title: '账号待平台管理员审核',
        icon: 'none'
      })
      return
    }

    if (detail?.status === 'rejected') {
      const reason = (detail.reject_reason || '').trim()
      uni.showToast({
        title: reason ? `平台管理员已驳回：${reason}` : '平台管理员已驳回',
        icon: 'none',
        duration: 3000
      })
    }
  } finally {
    loading.value = false
  }
}

function chooseRole(role) {
  registerForm.value.role = role
  registerForm.value.company_id = ''

  if (role.indexOf('merchant') === 0) {
    registerForm.value.company_type = 'merchant'
  } else if (role.indexOf('recycler') === 0) {
    registerForm.value.company_type = 'recycler'
  } else {
    registerForm.value.company_type = 'platform'
    registerForm.value.company_id = 0
  }
}

function handleCompanyChange(event) {
  const index = Number(event.detail.value)
  const company = currentCompanyList.value[index]

  if (company) {
    registerForm.value.company_id = company.id
  }
}

async function handleRegister() {
  if (!agreed.value) {
    uni.showToast({
      title: '请先阅读并同意《用户服务协议》和《隐私政策》',
      icon: 'none'
    })
    return
  }

  if (!registerForm.value.phone) {
    uni.showToast({
      title: '请输入手机号',
      icon: 'none'
    })
    return
  }

  if (!registerForm.value.nickname) {
    uni.showToast({
      title: '请输入昵称',
      icon: 'none'
    })
    return
  }

  if (!registerForm.value.password) {
    uni.showToast({
      title: '请设置密码',
      icon: 'none'
    })
    return
  }

  if (registerForm.value.password.length < 3) {
    uni.showToast({
      title: '密码至少3位',
      icon: 'none'
    })
    return
  }

  if (registerForm.value.password !== confirmPassword.value) {
    uni.showToast({
      title: '两次密码不一致',
      icon: 'none'
    })
    return
  }

  if (!registerForm.value.role) {
    uni.showToast({
      title: '请选择申请身份',
      icon: 'none'
    })
    return
  }

  if (needCompany.value) {
    if (isOwnerRole.value) {
      if (!newCompanyName.value.trim()) {
        uni.showToast({ title: '请输入公司名称', icon: 'none' })
        return
      }
    } else if (!registerForm.value.company_id) {
      uni.showToast({ title: '请选择所属公司', icon: 'none' })
      return
    }
  }

  if (loading.value) {
    return
  }

  loading.value = true

  try {
    await register({
      phone: registerForm.value.phone,
      nickname: registerForm.value.nickname,
      password: registerForm.value.password,
      role: registerForm.value.role,
      company_type: registerForm.value.company_type,
      company_id: (isOwnerRole.value) ? null : (Number(registerForm.value.company_id) || null),
      new_company_name: (isOwnerRole.value) ? newCompanyName.value.trim() : null,
      apply_reason: registerForm.value.apply_reason || ''
    })

    uni.showToast({
      title: '注册成功，请等待平台管理员审核',
      icon: 'success'
    })

    loginPhone.value = registerForm.value.phone
    loginPassword.value = ''
    confirmPassword.value = ''
    newCompanyName.value = ''
    companyMode.value = 'new'

    registerForm.value = {
      phone: '',
      nickname: '',
      password: '',
      role: '',
      company_type: '',
      company_id: '',
      apply_reason: ''
    }

    mode.value = 'login'
  } catch (error) {
    // 错误提示由 request.js 统一处理
  } finally {
    loading.value = false
  }
}

function resetData() {
  uni.showModal({
    title: '重新初始化',
    content: '会清空本地测试账号，只保留平台管理员账号。确定继续吗？',
    confirmColor: '#4b5563',
    success: res => {
      if (res.confirm) {
        state.value = resetAccountState()

        uni.removeStorageSync('token')
        uni.removeStorageSync('userInfo')
        uni.removeStorageSync('currentUser')

        loginPhone.value = '30001'
        loginPassword.value = ''

        uni.showToast({
          title: '已初始化',
          icon: 'success'
        })
      }
    }
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
  padding: 56rpx 34rpx 96rpx;
  padding-top: calc(var(--status-bar-height) + 56rpx);
  background: #17324d;
  color: #ffffff;
  border-radius: 0 0 48rpx 48rpx;
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.hello {
  font-size: 28rpx;
  opacity: 0.9;
  margin-bottom: 12rpx;
}

.title {
  font-size: 48rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
}

.mini-program-pill {
  height: 64rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: #222222;
  display: flex;
  align-items: center;
  font-size: 24rpx;
  font-weight: bold;
}

.phone-icon {
  width: 38rpx;
  height: 38rpx;
  margin-right: 10rpx;
  border-radius: 50%;
  background: #27b9ff;
  color: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24rpx;
}

.stats-row {
  display: flex;
  align-items: center;
  margin-top: 58rpx;
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-number {
  font-size: 44rpx;
  font-weight: 600;
}

.stat-label {
  margin-top: 8rpx;
  font-size: 24rpx;
  opacity: 0.9;
}

.stat-line {
  width: 1rpx;
  height: 48rpx;
  background: rgba(255, 255, 255, 0.5);
}

.main-card {
  margin: -52rpx 28rpx 40rpx;
  padding: 34rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
}

.mode-tabs {
  display: flex;
  padding: 8rpx;
  margin-bottom: 34rpx;
  border-radius: 999rpx;
  background: #f1f7fc;
}

.mode-tab {
  flex: 1;
  height: 72rpx;
  line-height: 72rpx;
  text-align: center;
  border-radius: 999rpx;
  color: #64748b;
  font-size: 28rpx;
  font-weight: bold;
}

.mode-tab.active {
  background: #17324d;
  color: #ffffff;
  box-shadow: none;
}

.section-title {
  font-size: 38rpx;
  font-weight: 600;
  color: #111111;
  margin-bottom: 12rpx;
}

.section-desc {
  color: #64748b;
  font-size: 26rpx;
  line-height: 40rpx;
  margin-bottom: 32rpx;
}

.form-item {
  margin-bottom: 28rpx;
}

.label {
  color: #333333;
  font-size: 26rpx;
  font-weight: bold;
  margin-bottom: 14rpx;
}

.input,
.textarea,
.picker-box {
  width: 100%;
  background: #f5f8fb;
  border-radius: 24rpx;
  box-sizing: border-box;
}

.input {
  height: 90rpx;
  padding: 0 26rpx;
  font-size: 30rpx;
}

.textarea {
  min-height: 150rpx;
  padding: 24rpx 26rpx;
  font-size: 28rpx;
}

.picker-box {
  height: 90rpx;
  padding: 0 26rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #333333;
  font-size: 28rpx;
}

.picker-arrow {
  color: #999999;
}

.agreement-row {
  display: flex;
  align-items: flex-start;
  margin: 8rpx 0 24rpx;
  padding: 0 4rpx;
}
.agree-box {
  width: 34rpx;
  height: 34rpx;
  border: 2rpx solid #b0b6bf;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14rpx;
  margin-top: 2rpx;
  flex-shrink: 0;
}
.agree-box.checked {
  background: #17324d;
  border-color: #17324d;
}
.agree-tick {
  color: #ffffff;
  font-size: 24rpx;
  line-height: 1;
}
.agree-text {
  flex: 1;
  font-size: 24rpx;
  color: #6b7280;
  line-height: 36rpx;
}
.agree-link {
  color: #1d9eff;
}

.primary-btn {
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 999rpx;
  background: #17324d;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: bold;
  box-shadow: none;
}

.primary-btn::after {
  border: none;
}

.tips-box {
  margin-top: 34rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: #f6f7f9;
}

.tips-title {
  color: #111111;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 12rpx;
}

.tips-line {
  color: #777777;
  font-size: 24rpx;
  line-height: 38rpx;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.role-card {
  padding: 24rpx;
  border-radius: 16rpx;
  background: #f6f7f9;
  border: 2rpx solid transparent;
}

.role-card.active {
  background: #eaf7ff;
  border-color: #17324d;
}

.role-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 20rpx;
  background: #17324d;
  color: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 18rpx;
}

.role-name {
  color: #111111;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 8rpx;
}

.role-desc {
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
}

.float-btn {
  position: fixed;
  right: 34rpx;
  bottom: 70rpx;
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: #17324d;
  color: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 42rpx;
  box-shadow: none;
}
.company-mode-tabs {
  display: flex;
  background: #f0f4f8;
  border-radius: 16rpx;
  padding: 6rpx;
  margin-bottom: 8rpx;
}
.company-mode-tab {
  flex: 1;
  text-align: center;
  padding: 12rpx 0;
  border-radius: 12rpx;
  font-size: 26rpx;
  color: #888;
}
.company-mode-tab.active {
  background: #fff;
  color: #17324d;
  font-weight: bold;
}


.page .hero{margin:0;padding:calc(var(--status-bar-height) + 64rpx) 40rpx 64rpx;border-radius:0}
.page .main-card{margin:24rpx;padding:32rpx;border-radius:16rpx}


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
