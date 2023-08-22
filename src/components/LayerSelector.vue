<script setup lang="ts">
import type { SelectableItem, SelectableGroupItem, SelectableSingleItem } from '@/utils/layerSelector'
import { watch, ref, computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string[]
    items?: SelectableItem[]
  }>(),
  {
    modelValue: () => [],
    items: () => []
  }
)
const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>()

const themeIdx = ref<number>()
const themeItems = computed<any[]>(() =>
  props.items?.filter((item: any) => item.id === 'theme')
    .flatMap((item: any) => item.children)
)

const tab = ref<string>()
const tabItems = computed<any[]>(() =>
  props.items?.filter((item: any) => item.tab)
    .flatMap((item: any) => item.children)
)

watch([themeIdx, tab], () => {
  updateLayers()
})

watch(() => props.items,
  (value: SelectableItem[]) => {
    // init with default selected theme
    const themeGroup = value.find((item: SelectableItem) => item.id === 'theme')
    if (themeGroup) {
      (themeGroup as SelectableGroupItem).children.forEach((item: SelectableSingleItem, index: number) => {
      if (item.selected)
        themeIdx.value = index
      })
    }
    // init with first map
    const firstTab = value.filter((item: SelectableItem) => (item as SelectableGroupItem).tab)[0] as SelectableGroupItem
    if (firstTab && firstTab.children)
      tab.value = firstTab.children[0].id      
    updateLayers()
  },
  { immediate: true }
)

function updateLayers() {
  const sels = []
  if (themeIdx.value !== undefined) {
    sels.push(themeItems.value[themeIdx.value].id)
  }
  if (tab.value) { 
    const map = tabItems.value.filter((item: SelectableItem) => item.id === tab.value).pop()
    if (map) {
      sels.push(map.id)
    }
  }
  emit('update:modelValue', sels)
}

</script>

<template>
  <v-card flat>
    <v-card-text class="pa-0">
      <div>
        <div class="mb-2 text-overline">Theme</div>
        <v-btn-toggle
          v-model="themeIdx"
          divided
          variant="outlined"
        >
          <v-btn v-for="(item, index) in themeItems" :key="index" size="x-small">{{ item.label }}</v-btn>
        </v-btn-toggle>
      </div>
      <div class="mt-2">
        <div class="mb-2 text-overline">Trees</div>

        <v-select
          v-model="tab"
          label="Species"
          :items="tabItems"
          item-title="label"
          item-value="id"
          density="compact"
          class="mt-2"
        ></v-select>
      </div>

    </v-card-text>
  </v-card>
</template>
