// 检测组第一项为正常值，其他已选值归入异常；未知不得作为正常。
export const normalDeviceValues = {
  "powerOn": "正常开机",
  "idLock": "无 ID 锁",
  "screenLock": "无锁屏密码",
  "screenRepair": "屏幕无维修情况",
  "screenDisplay": "显示完美",
  "screenAppearance": "屏外观完美",
  "mainboard": "主板无维修情况",
  "batteryRepair": "电池无维修",
  "batteryHealth": "电池健康度100%",
  "backCoverRepair": "后壳无维修",
  "partsRepair": "功能零件无维修和缺失",
  "frame": "全新机",
  "water": "机身无进水",
  "bend": "机身无弯曲",
  "frontCameraRepair": "前摄像头无维修和缺失",
  "rearCameraRepair": "后摄像头无维修和缺失",
  "rearPhoto": "后摄拍照摄像正常",
  "charge": "充电正常",
  "sensor": "光线、距离感应正常",
  "compass": "指南针功能正常",
  "factory": "未激活",
  "touch": "触摸功能正常",
  "call": "通话功能正常",
  "vibration": "振动功能正常",
  "face": "面容识别功能正常",
  "wireless": "无线充电功能正常",
  "icloud": "ID已注销",
  "boot": "正常开机",
  "sideButton": "侧键正常"
}
export function isAbnormalDeviceValue(key, value) {
  return String(value).trim() !== normalDeviceValues[key]
}
