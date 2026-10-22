<template><trade-board ref="board" mode="merchant-order" :customer-view="customerView" /></template>
<script setup>
import { ref } from 'vue'
import { onLoad, onShow, onHide, onReady } from '@dcloudio/uni-app'
import TradeBoard from '@/components/trade-board/trade-board.vue'
const customerView = ref(false)
onLoad(options => { customerView.value = options.customer === '1' })
const board = ref(null)
onReady(() => board.value?.start())
onShow(() => board.value?.start())
onHide(() => board.value?.stop())
</script>
