<template>
  <view class="page">
    <custom-navbar title="设备估价" />

    <!-- 机大侠检测说明弹窗 -->
    <view v-if="showDetectModal" class="modal-mask">
      <view class="detect-modal">
        <view class="modal-title">功能检测说明</view>

        <view class="modal-desc">
          能开机的数码产品，请在被回收的手机上下载
          <text class="strong">机大侠助手</text>
          进行功能检测，并保留检测结果照片。该照片非必传，但会影响回收商报价准确性。
        </view>

        <view class="detect-list">
          <view
            class="detect-item"
            v-for="item in detectItems"
            :key="item"
          >
            {{ item }}
          </view>
        </view>

        <button class="modal-btn" @click="confirmDetectNotice">
          我知道了
        </button>
      </view>
    </view>

    <!-- 顶部业务卡片 -->
    <view class="hero-card">
      <view class="hero-top">
        <view>
          <view class="hero-label">设备询价单</view>
          <view class="hero-title">{{ titleText }}</view>
          <view class="hero-subtitle">
            {{ summaryText || '请选择物品信息，提交后由回收商人工报价' }}
          </view>
        </view>

        <view class="price-badge">
          ¥
        </view>
      </view>

      <view class="quote-card">
        <view>
          <view class="quote-label">回收商报价</view>
          <view class="quote-value">待报价</view>
        </view>

        <view class="quote-status">
          人工报价
        </view>
      </view>

      <view class="progress-box">
        <view class="progress-top">
          <text>填写进度</text>
          <text>{{ completedCount }} / {{ requiredFields.length }}</text>
        </view>

        <view class="progress-bar">
          <view
            class="progress-inner"
            :style="{ width: progressPercent + '%' }"
          ></view>
        </view>
      </view>

      <view class="notice">
        提交后将发送给全国回收商，由回收商人工报价，不自动生成估价。
      </view>
    </view>

    <!-- 选择物品信息 -->
    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">选择物品信息</view>
          <view class="section-desc">设备类型、品牌、型号与基础配置</view>
        </view>

        <view class="section-index">01</view>
      </view>

      <OptionRow
        label="设备类型"
        :options="deviceTypes"
        :value="form.deviceType"
        @select="selectDeviceType"
      />

      <OptionRow
        label="品牌"
        :options="currentBrands"
        :value="form.brand"
        @select="selectBrand"
      />

      <OptionRow
        label="型号"
        :options="currentModels"
        :value="modelDisplayValue"
        @select="selectModel"
      />

      <view v-if="showCustomModel" class="custom-box">
        <input
          class="custom-input"
          v-model="customModel"
          placeholder="请输入其他型号"
          placeholder-class="placeholder"
        />

        <button class="small-btn" @click="confirmCustomModel">
          确认型号
        </button>
      </view>

      <OptionRow
        label="购买渠道"
        :options="channelOptions"
        :value="form.channel"
        @select="value => selectOption('channel', value)"
      />

      <OptionRow
        label="存储容量"
        :options="storageOptions"
        :value="form.storage"
        @select="value => selectOption('storage', value)"
      />

      <OptionRow
        label="保修时长"
        :options="warrantyOptions"
        :value="form.warranty"
        @select="value => selectOption('warranty', value)"
      />

      <OptionRow
        label="机身颜色"
        :options="colorOptions"
        :value="form.color"
        @select="value => selectOption('color', value)"
      />
    </view>

    <!-- 开机情况总开关 -->
    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">开机情况</view>
          <view class="section-desc">无法开机将简化填写，由回收商看图报价</view>
        </view>
      </view>
      <OptionRow
        label="设备能否开机"
        :options="powerOnOptions"
        :value="form.powerOn"
        @select="value => selectOption('powerOn', value)"
      />
    </view>

    <!-- 无法开机：只看图报价，重点 ID锁/锁屏 -->
    <view class="section">
      <view class="section-title">成色</view>
      <view class="option-list">
        <view v-for="grade in conditionOptions" :key="grade" :class="['option-item', form.condition === grade ? 'selected' : '']" @click="form.condition = grade">{{ grade }}</view>
      </view>
    </view>
    <view v-if="form.powerOn === '无法开机'" class="section">
      <view class="section-head">
        <view>
          <view class="section-title">无法开机 · 关键信息</view>
          <view class="section-desc">回收商看图报价，重点确认 ID锁 / 锁屏密码能否解</view>
        </view>
      </view>
      <OptionRow
        label="ID 锁情况"
        :options="idLockOptions"
        :value="form.idLock"
        @select="value => selectOption('idLock', value)"
      />
      <OptionRow
        label="锁屏密码"
        :options="screenLockOptions"
        :value="form.screenLock"
        @select="value => selectOption('screenLock', value)"
      />
      <view class="lock-tip">无法开机的机器请把「照片上传 / 细节图」拍清机身四周、屏幕、背面，并在「补充说明」注明进水/摔过等已知情况，方便回收商报价。</view>
    </view>

    <!-- 成色情况 -->
    <view v-if="form.powerOn !== '无法开机'" class="section">
      <view class="section-head">
        <view>
          <view class="section-title">选择成色情况</view>
          <view class="section-desc">屏幕、主板、外壳和维修记录</view>
        </view>

        <view :class="['complete-tag', conditionComplete ? 'done' : '']">
          {{ conditionComplete ? '已完善' : '待完善' }}
        </view>
      </view>

      <OptionRow allow-other
        label="屏幕维修情况"
        :options="screenRepairOptions"
        :value="form.screenRepair"
        @select="value => selectOption('screenRepair', value)"
      />

      <OptionRow allow-other
        label="屏幕显示"
        :options="screenDisplayOptions"
        :value="form.screenDisplay"
        @select="value => selectOption('screenDisplay', value)"
      />

      <OptionRow allow-other
        label="主板维修情况"
        :options="mainboardOptions"
        :value="form.mainboard"
        @select="value => selectOption('mainboard', value)"
      />

      <OptionRow allow-other
        label="电池维修情况"
        :options="batteryRepairOptions"
        :value="form.batteryRepair"
        @select="value => selectOption('batteryRepair', value)"
      />

      <OptionRow allow-other
        label="屏幕外观"
        :options="screenAppearanceOptions"
        :value="form.screenAppearance"
        @select="value => selectOption('screenAppearance', value)"
      />

      <OptionRow allow-other
        label="后壳维修情况"
        :options="backCoverRepairOptions"
        :value="form.backCoverRepair"
        @select="value => selectOption('backCoverRepair', value)"
      />

      <OptionRow allow-other
        label="零件维修情况"
        :options="partsRepairOptions"
        :value="form.partsRepair"
        @select="value => selectOption('partsRepair', value)"
      />

      <OptionRow allow-other
        label="边框背板"
        :options="frameOptions"
        :value="form.frame"
        @select="value => selectOption('frame', value)"
      />

      <OptionRow allow-other
        label="受潮状况"
        :options="waterOptions"
        :value="form.water"
        @select="value => selectOption('water', value)"
      />

      <OptionRow allow-other
        label="机身弯曲情况"
        :options="bendOptions"
        :value="form.bend"
        @select="value => selectOption('bend', value)"
      />

      <OptionRow allow-other
        label="前摄维修情况"
        :options="frontCameraRepairOptions"
        :value="form.frontCameraRepair"
        @select="value => selectOption('frontCameraRepair', value)"
      />

      <OptionRow allow-other
        label="后摄维修情况"
        :options="rearCameraRepairOptions"
        :value="form.rearCameraRepair"
        @select="value => selectOption('rearCameraRepair', value)"
      />
    </view>

    <!-- 功能情况 -->
    <view v-if="form.powerOn !== '无法开机'" class="section">
      <view class="section-head">
        <view>
          <view class="section-title">请选择功能情况</view>
          <view class="section-desc">功能状态会影响回收商报价准确性</view>
        </view>

        <view :class="['complete-tag', functionComplete ? 'done' : '']">
          {{ functionComplete ? '已完善' : '待完善' }}
        </view>
      </view>

      <OptionRow allow-other
        label="充电功能"
        :options="chargeOptions"
        :value="form.charge"
        @select="value => selectOption('charge', value)"
      />

      <OptionRow allow-other
        label="屏幕传感器功能"
        :options="sensorOptions"
        :value="form.sensor"
        @select="value => selectOption('sensor', value)"
      />

      <OptionRow allow-other
        label="后摄拍摄功能"
        :options="rearPhotoOptions"
        :value="form.rearPhoto"
        @select="value => selectOption('rearPhoto', value)"
      />

      <OptionRow allow-other
        label="指南针功能"
        :options="compassOptions"
        :value="form.compass"
        @select="value => selectOption('compass', value)"
      />

      <OptionRow allow-other
        label="恢复出厂设置"
        :options="factoryOptions"
        :value="form.factory"
        @select="value => selectOption('factory', value)"
      />

      <OptionRow allow-other
        label="触摸功能"
        :options="touchOptions"
        :value="form.touch"
        @select="value => selectOption('touch', value)"
      />

      <OptionRow allow-other
        label="通话功能"
        :options="callOptions"
        :value="form.call"
        @select="value => selectOption('call', value)"
      />

      <OptionRow allow-other
        label="振动功能"
        :options="vibrationOptions"
        :value="form.vibration"
        @select="value => selectOption('vibration', value)"
      />

      <OptionRow allow-other
        label="面容识别功能"
        :options="faceOptions"
        :value="form.face"
        @select="value => selectOption('face', value)"
      />

      <OptionRow allow-other
        label="无线充电功能"
        :options="wirelessOptions"
        :value="form.wireless"
        @select="value => selectOption('wireless', value)"
      />

      <OptionRow allow-other
        label="电池健康度"
        :options="batteryHealthOptions"
        :value="form.batteryHealth"
        @select="value => selectOption('batteryHealth', value)"
      />

      <OptionRow allow-other
        label="ID是否可注销"
        :options="icloudOptions"
        :value="form.icloud"
        @select="value => selectOption('icloud', value)"
      />

      <OptionRow allow-other
        label="开机情况"
        :options="bootOptions"
        :value="form.boot"
        @select="value => selectOption('boot', value)"
      />

      <OptionRow allow-other
        label="侧键"
        :options="buttonOptions"
        :value="form.sideButton"
        @select="value => selectOption('sideButton', value)"
      />
    </view>

    <!-- 照片上传，全部非必传 -->
    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">照片上传</view>
          <view class="section-desc">非必传，但上传后报价更准确</view>
        </view>

        <view class="upload-tip">非必传</view>
      </view>

      <view class="upload-desc">
        建议上传本机系统界面、机身四周、正反面俯拍，以及爱思、沙漏、机大侠检测结果图。
      </view>

      <view class="photo-grid">
        <view
          class="photo-card"
          v-for="item in photoItems"
          :key="item.key"
        >
          <view class="photo-box" @click="choosePhoto(item.key)">
            <image
              v-if="form.photos[item.key]"
              class="photo-img"
              :src="form.photos[item.key]"
              mode="aspectFill"
            />

            <view v-else class="photo-empty">
              <view class="plus">+</view>
              <view class="photo-text">上传</view>
            </view>
          </view>

          <view class="photo-label">{{ item.label }}</view>

          <view
            v-if="form.photos[item.key]"
            class="remove-photo"
            @click="removePhoto(item.key)"
          >
            删除
          </view>
        </view>
      </view>

      <view class="detail-title">细节图，最多10张</view>

      <view class="detail-grid">
        <view
          class="detail-photo"
          v-for="(item, index) in form.photos.details"
          :key="index"
        >
          <image class="detail-img" :src="item" mode="aspectFill" />
          <view class="detail-remove" @click="removeDetailPhoto(index)">×</view>
        </view>

        <view
          v-if="form.photos.details.length < 10"
          class="detail-add"
          @click="chooseDetailPhotos"
        >
          <view class="plus">+</view>
          <view>上传细节图</view>
        </view>
      </view>
    </view>

    <!-- 备注 -->
    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">补充说明</view>
          <view class="section-desc">填写其他影响报价的问题</view>
        </view>
      </view>

      <textarea
        class="textarea"
        v-model="form.remark"
        placeholder="可填写其他问题，例如：进水、无法开机、摄像头有斑、边框磕碰等"
        placeholder-class="placeholder"
      ></textarea>
    </view>

    <view class="bottom-space"></view>

    <!-- 底部固定操作栏 -->
    <view class="bottom-bar">
      <view class="poster-btn" @click="downloadPoster">
        <text class="poster-icon">↓</text>
        <text>下载海报</text>
      </view>

      <button class="understand-btn" @click="showDetectModal = true">
        了解检测
      </button>

      <button
        :class="isFormComplete ? 'submit-btn' : 'submit-btn disabled'"
        @click="submitInquiry"
      >
        提交给回收商报价
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import OptionRow from '@/components/option-row/option-row.vue'
import { onShow } from '@dcloudio/uni-app'
import { createDevice } from '@/api/trade.js'
import { getNowText } from '@/utils/tradeFlow.js'
import { uploadImage } from '@/utils/request.js'

const currentUser = ref({})

const showDetectModal = ref(false)
const hasShownDetectModal = ref(false)
const showCustomModel = ref(false)
const customModel = ref('')

const form = ref({
  deviceType: '',
  brand: '',
  model: '',

  channel: '',
  storage: '',
  warranty: '',
  color: '',

  condition: '',
  powerOn: '正常开机',   // 正常开机 / 无法开机（无法开机走简化表单）
  idLock: '',            // 无法开机时：ID锁情况
  screenLock: '',        // 无法开机时：锁屏密码情况

  screenRepair: '',
  screenDisplay: '',
  mainboard: '',
  batteryRepair: '',
  screenAppearance: '',
  backCoverRepair: '',
  partsRepair: '',
  frame: '',
  water: '',
  bend: '',
  frontCameraRepair: '',
  rearCameraRepair: '',

  charge: '',
  sensor: '',
  rearPhoto: '',
  compass: '',
  factory: '',
  touch: '',
  call: '',
  vibration: '',
  face: '',
  wireless: '',
  batteryHealth: '',
  icloud: '',
  boot: '',
  sideButton: '',

  remark: '',
  testAppNoticeConfirmed: false,

  photos: {
    systemPage: '',
    side1: '',
    side2: '',
    top: '',
    chargingPort: '',
    leftBottom: '',
    leftTop: '',
    rightBottom: '',
    rightTop: '',
    frontTop: '',
    backTop: '',
    aisi: '',
    shalou: '',
    jdx: '',
    details: []
  }
})

onShow(() => {
  currentUser.value = uni.getStorageSync('userInfo') ||
    uni.getStorageSync('currentUser') ||
    {}

  if (!currentUser.value.role) {
    uni.reLaunch({
      url: '/pages/login/login'
    })
  }
})

const deviceTypes = ['手机', '平板', '电脑']

const brandMap = {
  手机: ['苹果', '华为', '小米', 'OPPO', 'vivo', '荣耀', '三星', '其他'],
  平板: ['苹果', '华为', '小米', '荣耀', '三星', '联想', '其他'],
  电脑: ['苹果', '联想', '戴尔', '惠普', '华硕', '小米', '华为', '其他']
}

const modelMap = {
  苹果: {
    手机: [
      'iPhone 17e',
      'iPhone 16 Pro Max',
      'iPhone 16 Pro',
      'iPhone 16',
      'iPhone 15 Pro Max',
      'iPhone 15 Pro',
      'iPhone 15',
      'iPhone 14 Pro Max',
      'iPhone 14',
      'iPhone 13',
      '其他'
    ],
    平板: ['iPad Pro', 'iPad Air', 'iPad mini', 'iPad 10', '其他'],
    电脑: ['MacBook Air', 'MacBook Pro 13', 'MacBook Pro 14', 'MacBook Pro 16', 'iMac', '其他']
  },
  华为: {
    手机: ['Mate 60 Pro', 'Mate 60', 'Pura 70', 'P60 Pro', 'P60', 'Mate 50', '其他'],
    平板: ['MatePad Pro', 'MatePad Air', 'MatePad 11', '其他'],
    电脑: ['MateBook X Pro', 'MateBook 14', 'MateBook D 14', 'MateBook D 16', '其他']
  },
  小米: {
    手机: ['小米 14 Pro', '小米 14', '小米 13', 'Redmi K70', 'Redmi K60', '其他'],
    平板: ['小米平板 6 Pro', '小米平板 6', 'Redmi Pad', '其他'],
    电脑: ['RedmiBook Pro', '小米笔记本 Pro', '其他']
  },
  OPPO: {
    手机: ['Find X7 Ultra', 'Find X7', 'Find X6', 'Reno 11', 'Reno 10', '其他']
  },
  vivo: {
    手机: ['X100 Pro', 'X100', 'X90 Pro', 'X90', 'S18', 'S17', '其他']
  },
  荣耀: {
    手机: ['Magic 6 Pro', 'Magic 6', 'Magic 5', '荣耀 100', '荣耀 90', '其他'],
    平板: ['荣耀平板 9', '荣耀平板 V8 Pro', '其他']
  },
  三星: {
    手机: ['Galaxy S24 Ultra', 'Galaxy S24', 'Galaxy S23 Ultra', 'Galaxy S23', '其他'],
    平板: ['Galaxy Tab S9', 'Galaxy Tab S8', '其他']
  },
  联想: {
    平板: ['小新 Pad Pro', '小新 Pad', '拯救者平板', '其他'],
    电脑: ['ThinkPad X1 Carbon', 'ThinkPad T14', '小新 Pro 14', '小新 Pro 16', '拯救者 Y7000P', '其他']
  },
  戴尔: {
    电脑: ['XPS 13', 'XPS 15', '灵越 14', '灵越 16', 'Latitude', '其他']
  },
  惠普: {
    电脑: ['战66', '星Book Pro', '暗影精灵', 'EliteBook', '其他']
  },
  华硕: {
    电脑: ['灵耀 14', '无畏 Pro', '天选', 'ROG 枪神', '其他']
  },
  其他: {
    手机: ['其他'],
    平板: ['其他'],
    电脑: ['其他']
  }
}

const channelOptions = ['大陆国行', '国行展示机', '港澳台', '国行官换', '海外版', '其他']
const storageOptions = ['64G', '128G', '256G', '512G', '1TB', '其他']
const warrantyOptions = ['≥330天', '180-329天', '30-179天', '<30天', '已过保', '不确定']
const colorOptions = ['浅粉色', '白色', '黑色', '蓝色', '金色', '银色', '其他']

const screenRepairOptions = ['屏幕无维修情况', '屏幕内部贴标/盖章/黑纸破损', '屏幕维修/更换']
const screenDisplayOptions = ['显示完美', '显示轻微老化', '显示亮点', '显示异常']
const mainboardOptions = ['主板无维修情况', '主板区域贴标/盖章/易损辅料缺损', '主板维修']
const batteryRepairOptions = ['电池无维修', '电池维修']
const screenAppearanceOptions = ['屏外观完美', '屏幕有细微划痕', '屏有划痕', '屏碎裂']
const backCoverRepairOptions = ['后壳无维修', '后壳破裂维修', '后壳总成维修']
const partsRepairOptions = ['功能零件无维修和缺失', '功能零件维修', '功能零件缺失']
const frameOptions = ['全新机', '外壳完美', '壳细微痕迹', '壳划痕/磕碰']
const waterOptions = ['机身无进水', '机身有受潮', '机身进水']
const bendOptions = ['机身无弯曲', '轻微弯曲', '明显弯曲']
const frontCameraRepairOptions = ['前摄像头无维修和缺失', '前摄像头维修', '前摄像头缺失']
const rearCameraRepairOptions = ['后摄像头无维修和缺失', '后摄像头维修', '后摄像头缺失']

const chargeOptions = ['充电正常', '不充电']
const sensorOptions = ['光线、距离感应正常', '光线/距离感应不正常']
const rearPhotoOptions = ['后摄拍照摄像正常', '后像头有斑', '后摄拍照有彩斑']
const compassOptions = ['指南针功能正常', '指南针功能不正常']
const factoryOptions = ['未激活', '预激活', '已激活，可还原', '已激活，不可还原']
const touchOptions = ['触摸功能正常', '触摸失灵/延迟']
const callOptions = ['通话功能正常', '通话功能正常但卡托破损/缺失', '通话异常']
const vibrationOptions = ['振动功能正常', '振动功能异常']
const faceOptions = ['面容识别功能正常', '面容无法录入和识别']
const wirelessOptions = ['无线充电功能正常', '无线充电功能异常']
const batteryHealthOptions = ['电池健康度100%', '电池健康95~99%', '电池健康90~94%', '电池健康80~89%', '低于80%']
const icloudOptions = ['ID已注销', 'ID无法注销']
const bootOptions = ['正常开机', '有开机密码', '可进入桌面，进入后问题']
// 开机情况总开关：无法开机走简化表单
const conditionOptions = ['准新机', '靓机', '小花', '大花', '外爆', '内爆', '内爆不测', '无法开机']
const powerOnOptions = ['正常开机', '无法开机']
// 无法开机时的关键项（回收商看图报价，重点看这两项能不能解）
const idLockOptions = ['无 ID 锁', '有 ID 锁', '未知']
const screenLockOptions = ['无锁屏密码', '有锁屏密码', '未知']
const buttonOptions = ['侧键正常', '侧键按压无反馈或失灵']

const detectItems = [
  '指南针',
  '振动功能',
  '重力感应器',
  'WIFI',
  '蓝牙',
  '距离感应器',
  '光线感应器',
  '闪光灯',
  '触摸功能',
  '主麦克风 / 后置麦克风',
  '扬声器',
  '听筒',
  '按键功能',
  '前置摄像头 / 后置摄像头',
  '屏幕显示',
  '指纹',
  '充电功能',
  '通话功能',
  '屏幕边界测试'
]

const photoItems = [
  { key: 'systemPage', label: '本机系统界面图' },
  { key: 'side1', label: '侧边1' },
  { key: 'side2', label: '侧边2' },
  { key: 'top', label: '顶端' },
  { key: 'chargingPort', label: '尾插' },
  { key: 'leftBottom', label: '左下角' },
  { key: 'leftTop', label: '左上角' },
  { key: 'rightBottom', label: '右下角' },
  { key: 'rightTop', label: '右上角' },
  { key: 'frontTop', label: '正面俯拍' },
  { key: 'backTop', label: '背面俯拍' },
  { key: 'aisi', label: '爱思检测图，苹果可选' },
  { key: 'shalou', label: '沙漏检测图，苹果可选' },
  { key: 'jdx', label: '机大侠检测图' }
]

// 物品信息（必填，无法开机也要）
const baseInfoFields = [
  { key: 'deviceType', label: '设备类型' },
  { key: 'brand', label: '品牌' },
  { key: 'model', label: '型号' },
  { key: 'channel', label: '购买渠道' },
  { key: 'storage', label: '存储容量' },
  { key: 'warranty', label: '保修时长' },
  { key: 'color', label: '机身颜色' }
]
// 成色 + 功能（仅正常开机需要）
const conditionFunctionFields = [
  { key: 'screenRepair', label: '屏幕维修情况' },
  { key: 'screenDisplay', label: '屏幕显示' },
  { key: 'mainboard', label: '主板维修情况' },
  { key: 'batteryRepair', label: '电池维修情况' },
  { key: 'screenAppearance', label: '屏幕外观' },
  { key: 'backCoverRepair', label: '后壳维修情况' },
  { key: 'partsRepair', label: '零件维修情况' },
  { key: 'frame', label: '边框背板' },
  { key: 'water', label: '受潮状况' },
  { key: 'bend', label: '机身弯曲情况' },
  { key: 'frontCameraRepair', label: '前摄维修情况' },
  { key: 'rearCameraRepair', label: '后摄维修情况' },
  { key: 'charge', label: '充电功能' },
  { key: 'sensor', label: '屏幕传感器功能' },
  { key: 'rearPhoto', label: '后摄拍摄功能' },
  { key: 'compass', label: '指南针功能' },
  { key: 'factory', label: '恢复出厂设置' },
  { key: 'touch', label: '触摸功能' },
  { key: 'call', label: '通话功能' },
  { key: 'vibration', label: '振动功能' },
  { key: 'face', label: '面容识别功能' },
  { key: 'wireless', label: '无线充电功能' },
  { key: 'batteryHealth', label: '电池健康度' },
  { key: 'icloud', label: 'ID是否可注销' },
  { key: 'boot', label: '开机情况' },
  { key: 'sideButton', label: '侧键' }
]
// 无法开机只需填物品信息；正常开机走完整 33 项
const requiredFields = computed(() => {
  return form.value.powerOn === '无法开机'
    ? baseInfoFields
    : [...baseInfoFields, ...conditionFunctionFields]
})

const currentBrands = computed(() => {
  return brandMap[form.value.deviceType] || []
})

const currentModels = computed(() => {
  const brand = form.value.brand
  const type = form.value.deviceType

  if (!modelMap[brand]) return ['其他']
  return modelMap[brand][type] || ['其他']
})

const modelDisplayValue = computed(() => {
  return showCustomModel.value ? '其他' : form.value.model
})

const titleText = computed(() => {
  if (form.value.brand && form.value.model) {
    return `${form.value.brand} ${form.value.model}`
  }

  if (form.value.brand) {
    return form.value.brand
  }

  return '请选择设备'
})

const summaryText = computed(() => {
  const device = form.value.brand && form.value.model
    ? `${form.value.brand} ${form.value.model}`
    : ''

  const arr = [
    device,
    form.value.storage,
    form.value.color,
    form.value.channel,
    form.value.warranty ? `保修${form.value.warranty}` : ''
  ]

  return arr.filter(Boolean).join(' · ')
})

function isFilledDetection(value) {
  const text = String(value || '').trim()
  return !!text && text !== '其他' && !(text.startsWith('其他：') && !text.slice(3).trim())
}
const missingFields = computed(() => {
  return requiredFields.value.filter(item => {
    return !isFilledDetection(form.value[item.key])
  })
})

const completedCount = computed(() => {
  return requiredFields.value.length - missingFields.value.length
})

const progressPercent = computed(() => {
  return Math.round((completedCount.value / requiredFields.value.length) * 100)
})

const isFormComplete = computed(() => {
  return missingFields.value.length === 0
})

const conditionComplete = computed(() => {
  if (conditionFunctionFields.slice(0,12).some(({key}) => !isFilledDetection(form.value[key]))) return false
  return Boolean(
    form.value.screenRepair &&
    form.value.screenDisplay &&
    form.value.mainboard &&
    form.value.batteryRepair &&
    form.value.screenAppearance &&
    form.value.backCoverRepair &&
    form.value.partsRepair &&
    form.value.frame &&
    form.value.water &&
    form.value.bend &&
    form.value.frontCameraRepair &&
    form.value.rearCameraRepair
  )
})

const functionComplete = computed(() => {
  if (conditionFunctionFields.slice(12).some(({key}) => !isFilledDetection(form.value[key]))) return false
  return Boolean(
    form.value.charge &&
    form.value.sensor &&
    form.value.rearPhoto &&
    form.value.compass &&
    form.value.factory &&
    form.value.touch &&
    form.value.call &&
    form.value.vibration &&
    form.value.face &&
    form.value.wireless &&
    form.value.batteryHealth &&
    form.value.icloud &&
    form.value.boot &&
    form.value.sideButton
  )
})

const phoneSituationComplete = computed(() => {
  return conditionComplete.value && functionComplete.value
})

watch(phoneSituationComplete, (value) => {
  if (value && !hasShownDetectModal.value) {
    showDetectModal.value = true
    hasShownDetectModal.value = true
  }
})

function confirmDetectNotice() {
  form.value.testAppNoticeConfirmed = true
  showDetectModal.value = false
}

function selectDeviceType(value) {
  form.value.deviceType = value
  form.value.brand = ''
  form.value.model = ''
  showCustomModel.value = false
  customModel.value = ''
}

function selectBrand(value) {
  form.value.brand = value
  form.value.model = ''
  showCustomModel.value = false
  customModel.value = ''
}

function selectModel(value) {
  if (value === '其他') {
    showCustomModel.value = true
    form.value.model = ''
    return
  }

  showCustomModel.value = false
  customModel.value = ''
  form.value.model = value
}

function confirmCustomModel() {
  if (!customModel.value) {
    uni.showToast({
      title: '请输入型号',
      icon: 'none'
    })
    return
  }

  form.value.model = customModel.value
  showCustomModel.value = false
}

function selectOption(key, value) {
  form.value[key] = value
}

function choosePhoto(key) {
  uni.chooseImage({
    count: 1,
    success(res) {
      const tempPath = res.tempFilePaths[0]
      // 先用本地临时路径占位预览，再异步上传换成服务器地址
      form.value.photos[key] = tempPath

      uni.showLoading({ title: '上传中', mask: true })
      uploadImage(tempPath)
        .then(url => {
          form.value.photos[key] = url
        })
        .catch(() => {
          // 上传失败时保留本地预览，不阻断流程
        })
        .finally(() => {
          uni.hideLoading()
        })
    }
  })
}

function removePhoto(key) {
  form.value.photos[key] = ''
}

function chooseDetailPhotos() {
  const currentCount = form.value.photos.details.length
  const remainCount = 10 - currentCount

  if (remainCount <= 0) {
    uni.showToast({
      title: '最多上传10张细节图',
      icon: 'none'
    })
    return
  }

  uni.chooseImage({
    count: remainCount,
    success(res) {
      const startIndex = form.value.photos.details.length
      form.value.photos.details = form.value.photos.details.concat(res.tempFilePaths)

      uni.showLoading({ title: '上传中', mask: true })
      Promise.all(
        res.tempFilePaths.map((path, i) =>
          uploadImage(path)
            .then(url => {
              form.value.photos.details[startIndex + i] = url
            })
            .catch(() => {})
        )
      ).finally(() => {
        uni.hideLoading()
      })
    }
  })
}

function removeDetailPhoto(index) {
  form.value.photos.details.splice(index, 1)
}

function downloadPoster() {
  uni.showToast({
    title: '海报功能后续接入',
    icon: 'none'
  })
}

function submitInquiry() {
  const emptyOther = conditionFunctionFields.find(({key}) => form.value[key] === '其他' || (String(form.value[key] || '').startsWith('其他：') && !String(form.value[key]).slice(3).trim()))
  if (emptyOther) { uni.showToast({title: '请填写' + emptyOther.label + '的其他异常情况', icon:'none'}); return }

  if (!form.value.condition) { uni.showToast({ title: '请选择成色', icon: 'none' }); return }
  if (showCustomModel.value && !customModel.value) {
    uni.showToast({
      title: '请输入其他型号',
      icon: 'none'
    })
    return
  }

  if (missingFields.value.length > 0) {
    const names = missingFields.value.map(item => item.label)

    uni.showModal({
      title: '信息未填写完整',
      content: `请先选择：${names.slice(0, 8).join('、')}${names.length > 8 ? '等' : ''}`,
      showCancel: false,
      confirmText: '知道了'
    })

    return
  }

  if (!form.value.photos.jdx) {
    uni.showModal({
      title: '建议上传机大侠助手检测图',
      content: '检测图非必传，但会影响回收商报价准确性。未上传检测结果也可以提交。',
      cancelText: '去上传',
      confirmText: '仍然提交',
      success(res) {
        if (res.confirm) {
          doSubmitInquiry()
        }
      }
    })

    return
  }

  doSubmitInquiry()
}

function collectImageList(photos) {
  if (!photos) {
    return []
  }

  const list = []

  Object.keys(photos).forEach(key => {
    const value = photos[key]

    if (!value) {
      return
    }

    if (Array.isArray(value)) {
      value.forEach(item => {
        if (item) {
          list.push(item)
        }
      })
      return
    }

    list.push(value)
  })

  return list
}

function buildDevicePayload() {
  const modelName = form.value.model === '其他型号'
    ? (customModel.value || '其他型号')
    : form.value.model

  const powerNote = form.value.powerOn === '无法开机' ? '【无法开机】' : ''
  const faultDesc = (powerNote + (form.value.remark || '')).trim() ||
    (form.value.powerOn === '无法开机' ? '无法开机，看图报价' : '无明显故障')

  return {
    device_type: form.value.deviceType,
    brand: form.value.brand,
    model: modelName,
    condition: form.value.condition,
    fault_desc: faultDesc,
    images: collectImageList(form.value.photos),
    recyclerCompanyIds: [],
    storage: form.value.storage || '',
    color: form.value.color || '',
    channel: form.value.channel || '',
    warranty: form.value.warranty || '',
    detail: buildDeviceDetail()
  }
}

// 逐项检测结果:与设备详情页字段一一对应，只收集已填写的项
const DEVICE_DETAIL_KEYS = [
  'powerOn', 'idLock', 'screenLock',
  'screenRepair', 'screenDisplay', 'screenAppearance', 'mainboard',
  'batteryRepair', 'batteryHealth', 'backCoverRepair', 'partsRepair',
  'frame', 'water', 'bend', 'frontCameraRepair', 'rearCameraRepair',
  'rearPhoto', 'charge', 'sensor', 'compass', 'factory', 'touch',
  'call', 'vibration', 'face', 'wireless', 'icloud', 'boot', 'sideButton'
]

function buildDeviceDetail() {
  const detail = {}

  DEVICE_DETAIL_KEYS.forEach(key => {
    const value = form.value[key]
    if (value !== undefined && value !== null && value !== '') {
      detail[key] = value
    }
  })

  return detail
}

async function doSubmitInquiry() {
  try {
    await createDevice(buildDevicePayload())

    uni.showToast({
      title: '发布成功，已生成询价',
      icon: 'success'
    })

    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/merchant/order/order?tab=pendingQuote'
      })
    }, 600)

    return
  } catch (error) {
    return // 服务端拒绝时不得生成本地询价
  }

  const inquiryList = uni.getStorageSync('inquiryList') || []
  const merchantCompany = getCurrentMerchantCompany()

  const inquiry = {
    id: Date.now(),
    no: `XJ${Date.now()}`,
    merchantCompanyId: merchantCompany.id,
    merchantCompanyName: merchantCompany.name,
    merchantUserId: merchantCompany.userId,
    merchantUserRole: merchantCompany.userRole,
    recyclerCompanyIds: [],
    recyclerCompanyNames: [],
    status: '待报价',
    quoteStatus: 'pending_quote',
    deviceType: form.value.deviceType,
    brand: form.value.brand,
    model: form.value.model,
    channel: form.value.channel,
    storage: form.value.storage,
    warranty: form.value.warranty,
    color: form.value.color,
    screenRepair: form.value.screenRepair,
    screenDisplay: form.value.screenDisplay,
    mainboard: form.value.mainboard,
    batteryRepair: form.value.batteryRepair,
    screenAppearance: form.value.screenAppearance,
    backCoverRepair: form.value.backCoverRepair,
    partsRepair: form.value.partsRepair,
    frame: form.value.frame,
    water: form.value.water,
    bend: form.value.bend,
    frontCameraRepair: form.value.frontCameraRepair,
    rearCameraRepair: form.value.rearCameraRepair,
    charge: form.value.charge,
    sensor: form.value.sensor,
    rearPhoto: form.value.rearPhoto,
    compass: form.value.compass,
    factory: form.value.factory,
    touch: form.value.touch,
    call: form.value.call,
    vibration: form.value.vibration,
    face: form.value.face,
    wireless: form.value.wireless,
    batteryHealth: form.value.batteryHealth,
    icloud: form.value.icloud,
    boot: form.value.boot,
    sideButton: form.value.sideButton,
    remark: form.value.remark,
    testAppNoticeConfirmed: form.value.testAppNoticeConfirmed,
    photos: form.value.photos,
    createTime: getNowText(),
    validUntil: getTodayEndTime()
  }

  inquiryList.unshift(inquiry)
  uni.setStorageSync('inquiryList', inquiryList)

  uni.showToast({
    title: '已提交给回收商',
    icon: 'success'
  })

  setTimeout(() => {
    uni.navigateTo({
      url: '/pages/merchant/order/order?tab=pendingQuote'
    })
  }, 600)
}

function getCurrentMerchantCompany() {
  return {
    id: currentUser.value.company_id || uni.getStorageSync('merchantCompanyId') || 'M001',
    name: currentUser.value.company_name || uni.getStorageSync('merchantCompanyName') || '默认商家公司',
    userId: currentUser.value.id || uni.getStorageSync('userId') || 'merchant_boss_001',
    userRole: currentUser.value.role || uni.getStorageSync('userRole') || 'merchant_owner'
  }
}

function getTodayEndTime() {
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')

  return `${yyyy}-${mm}-${dd} 23:59:59`
}

// OptionRow 已改为模板组件 components/option-row/option-row.vue（h() 渲染函数在微信小程序上不响应点击，故重构）
</script>




<style scoped>

.option-list{display:flex;flex-wrap:wrap;gap:16rpx}.option-item{padding:16rpx 26rpx;background:#f3f5f8;border-radius:16rpx;font-size:26rpx}.option-item.selected{background:#344054;color:#fff}
.page {
  min-height: 100vh;
  background: #f5f8fb;
  padding-bottom: 170rpx;
  box-sizing: border-box;
}

.hero-card {
  margin: 24rpx 24rpx 0;
  padding: 30rpx;
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

.hero-label {
  display: inline-flex;
  height: 46rpx;
  line-height: 46rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.24);
  font-size: 24rpx;
  font-weight: bold;
  margin-bottom: 18rpx;
}

.hero-title {
  font-size: 44rpx;
  font-weight: 600;
  line-height: 1.25;
}

.hero-subtitle {
  margin-top: 12rpx;
  font-size: 25rpx;
  line-height: 38rpx;
  opacity: 0.92;
}

.price-badge {
  width: 82rpx;
  height: 82rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.24);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42rpx;
  font-weight: 600;
}

.quote-card {
  margin-top: 28rpx;
  padding: 26rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.quote-label {
  font-size: 24rpx;
  opacity: 0.92;
}

.quote-value {
  margin-top: 8rpx;
  font-size: 46rpx;
  font-weight: 600;
}

.quote-status {
  height: 52rpx;
  line-height: 52rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: #374151;
  font-size: 24rpx;
  font-weight: bold;
}

.progress-box {
  margin-top: 26rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.16);
}

.progress-top {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  font-weight: bold;
  margin-bottom: 14rpx;
}

.progress-bar {
  height: 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.28);
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  border-radius: 999rpx;
  background: #ffffff;
  transition: width 0.2s ease;
}

.notice {
  margin-top: 20rpx;
  font-size: 24rpx;
  line-height: 36rpx;
  opacity: 0.9;
}

.section {
  margin: 24rpx 24rpx 0;
  padding: 30rpx 0 8rpx;
  border-radius: 16rpx;
  background: #ffffff;
  box-shadow: none;
  overflow: hidden;
}

.lock-tip {
  margin: 8rpx 30rpx 20rpx;
  padding: 18rpx 22rpx;
  background: rgba(245, 108, 108, 0.08);
  color: #d9531e;
  font-size: 24rpx;
  line-height: 36rpx;
  border-radius: 16rpx;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0 30rpx 24rpx;
}

.section-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #222222;
}

.section-desc {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #64748b;
  line-height: 34rpx;
}

.section-index {
  color: #d6e8f4;
  font-size: 44rpx;
  font-weight: 600;
}

.complete-tag,
.upload-tip {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #fff7e6;
  color: #d97706;
  font-size: 24rpx;
  font-weight: bold;
}

.complete-tag.done {
  background: #ecfdf3;
  color: #18a058;
}

.option-row {
  padding: 26rpx 30rpx;
  border-top: 1rpx solid #eef3f6;
  background: #ffffff;
  display: block;
  box-sizing: border-box;
}

.option-label {
  display: block;
  width: 100%;
  color: #222222;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 18rpx;
  line-height: 40rpx;
}

.options-wrap {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  align-items: flex-start;
  box-sizing: border-box;
}

.option-item {
  min-height: 60rpx;
  line-height: 60rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: #f4f8fb;
  color: #60656f;
  font-size: 25rpx;
  border: 2rpx solid transparent;
  box-sizing: border-box;
  white-space: nowrap;
  flex-shrink: 0;
}

.option-item.active {
  background: #eef0f4;
  color: #374151;
  border-color: #17324d;
  font-weight: bold;
}

.custom-box {
  margin: 0 30rpx 20rpx;
  background: #f6f7f9;
  border-radius: 24rpx;
  padding: 22rpx;
  box-sizing: border-box;
}

.custom-input {
  width: 100%;
  height: 82rpx;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 0 22rpx;
  margin-bottom: 16rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.small-btn {
  background: #17324d;
  color: #ffffff;
  border-radius: 999rpx;
  font-size: 28rpx;
  height: 72rpx;
  line-height: 72rpx;
}

.small-btn::after {
  border: none;
}

.upload-desc {
  margin: 0 30rpx 24rpx;
  color: #64748b;
  font-size: 25rpx;
  line-height: 38rpx;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24rpx 18rpx;
  padding: 0 30rpx 28rpx;
  box-sizing: border-box;
}

.photo-card {
  text-align: center;
}

.photo-box {
  height: 150rpx;
  background: #f6f7f9;
  border: 2rpx dashed #dce8f0;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.photo-img {
  width: 100%;
  height: 100%;
}

.photo-empty {
  color: #9aa6b2;
  font-size: 24rpx;
}

.plus {
  font-size: 42rpx;
  line-height: 42rpx;
  color: #9aa6b2;
}

.photo-text {
  margin-top: 8rpx;
}

.photo-label {
  margin-top: 10rpx;
  color: #666666;
  font-size: 24rpx;
  line-height: 32rpx;
  min-height: 64rpx;
}

.remove-photo {
  margin-top: 6rpx;
  color: #ff5a3c;
  font-size: 24rpx;
}

.detail-title {
  padding: 0 30rpx 18rpx;
  color: #222222;
  font-size: 30rpx;
  font-weight: 600;
}

.detail-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 18rpx;
  padding: 0 30rpx 28rpx;
}

.detail-photo,
.detail-add {
  width: 150rpx;
  height: 150rpx;
  border-radius: 22rpx;
  background: #f6f7f9;
  border: 2rpx dashed #dce8f0;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9aa6b2;
  font-size: 24rpx;
  flex-direction: column;
  overflow: hidden;
}

.detail-img {
  width: 100%;
  height: 100%;
}

.detail-remove {
  position: absolute;
  right: 8rpx;
  top: 8rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #ffffff;
  font-size: 26rpx;
  text-align: center;
  line-height: 36rpx;
}

.textarea {
  margin: 0 30rpx 26rpx;
  width: calc(100% - 60rpx);
  min-height: 160rpx;
  background: #f6f7f9;
  border-radius: 24rpx;
  padding: 22rpx;
  box-sizing: border-box;
  font-size: 28rpx;
  line-height: 42rpx;
  color: #222222;
}

.placeholder {
  color: #b6bdc6;
}

.bottom-space {
  height: 150rpx;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  min-height: 118rpx;
  background: rgba(255, 255, 255, 0.96);
  border-top: 1rpx solid #eef1f4;
  display: flex;
  align-items: center;
  padding: 16rpx 22rpx calc(18rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  z-index: 20;
  gap: 16rpx;
}

.poster-btn {
  width: 118rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-right: 0;
  color: #444444;
  font-size: 24rpx;
}

.poster-icon {
  font-size: 34rpx;
  line-height: 34rpx;
}

.understand-btn {
  flex: 1;
  height: 78rpx;
  line-height: 78rpx;
  border: 2rpx solid #17324d;
  color: #374151;
  background: #ffffff;
  border-radius: 999rpx;
  font-size: 27rpx;
  margin: 0;
  font-weight: bold;
}

.submit-btn {
  flex: 1.25;
  height: 78rpx;
  line-height: 78rpx;
  background: #17324d;
  color: #ffffff;
  border-radius: 999rpx;
  font-size: 27rpx;
  margin: 0;
  font-weight: bold;
  box-shadow: none;
}

.understand-btn::after,
.submit-btn::after,
.modal-btn::after {
  border: none;
}

.submit-btn.disabled {
  background: #d5dce3;
  color: #ffffff;
  box-shadow: none;
}

.modal-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  box-sizing: border-box;
}

.detect-modal {
  width: 100%;
  max-height: 80vh;
  background: #ffffff;
  border-radius: 16rpx;
  padding: 38rpx 30rpx 30rpx;
  box-sizing: border-box;
  overflow-y: auto;
}

.modal-title {
  font-size: 38rpx;
  font-weight: 600;
  color: #222222;
  margin-bottom: 20rpx;
  text-align: center;
}

.modal-desc {
  font-size: 28rpx;
  color: #555555;
  line-height: 44rpx;
  margin-bottom: 24rpx;
}

.strong {
  color: #374151;
  font-weight: bold;
}

.detect-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 30rpx;
}

.detect-item {
  background: #eef0f4;
  color: #374151;
  border: 1rpx solid #b7e8ff;
  border-radius: 999rpx;
  padding: 12rpx 18rpx;
  font-size: 25rpx;
}

.modal-btn {
  background: #17324d;
  color: #ffffff;
  border-radius: 999rpx;
  height: 82rpx;
  line-height: 82rpx;
  font-size: 30rpx;
  font-weight: bold;
}

.select-all-btn {
  padding: 10rpx 22rpx;
  border-radius: 999rpx;
  background: #eef0f4;
  color: #374151;
  font-size: 24rpx;
  font-weight: bold;
}

.recycler-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
  padding: 0 30rpx;
}

.recycler-chip {
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f6f7f9;
  border: 2rpx solid transparent;
}

.recycler-chip.active {
  background: #eaf7ff;
  border-color: #17324d;
}

.recycler-name {
  color: #111111;
  font-size: 28rpx;
  font-weight: bold;
}

.recycler-meta {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.recycler-tip {
  margin: 20rpx 30rpx 10rpx;
  color: #666666;
  font-size: 24rpx;
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
