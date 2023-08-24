<script setup lang="ts">
import JsonWebMap from '@/components/JsonWebMap.vue'
import { useConfigurationStore } from '@/stores/configuration'

const { parametersUrl, styleUrl, cdnUrl } = useConfigurationStore()
</script>

<template>
  <JsonWebMap :parameters-url="parametersUrl" :style-url="styleUrl" :cdn-url="cdnUrl" />
</template>
