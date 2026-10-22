<template><trade-board ref="board" mode="recycler-inquiry" /></template>
<script setup>
import { ref } from 'vue'
import { onShow, onHide, onReady } from '@dcloudio/uni-app'
import TradeBoard from '@/components/trade-board/trade-board.vue'
const board = ref(null)
onReady(() => board.value?.start())
onShow(() => board.value?.start())
onHide(() => board.value?.stop())
</script>
