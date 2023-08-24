<script setup lang="ts">
import type { SelectableItem, SelectableGroupItem, SelectableSingleItem, SpeciesItem } from '@/utils/layerSelector'
import { watch, ref, computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string[]
    items?: SelectableItem[],
    species: SpeciesItem[]
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

const genre = ref<string>()
const genreItems = computed<any[]>(() =>
  props.species
    .map((item) => item.GENRE_lat)
    .filter((value, index, array) => array.indexOf(value) === index)
    .map((g) => { return { id: g.toLowerCase().replace(' ', '_'), label: g }})
)

const tab = ref<string>()
const tabItems = computed<SelectableItem[]>(() =>
  props.items?.filter((item: SelectableItem) => (item as SelectableGroupItem).tab)
    .flatMap((item: SelectableItem) => (item as SelectableGroupItem).children)
    .filter((item: SelectableSingleItem) => item.genre === genre.value) // filter species by selected genre
)

watch(genre, () => {
  // select the default species or the first one
  const selected = tabItems.value.find((item: SelectableItem) => item.selected)
  tab.value = selected ? selected.id : tabItems.value[0].id
})

watch([themeIdx, tab], () => {
  updateLayers()
})

watch(() => props.items,
  (value: SelectableItem[]) => {
    // init with default selected theme
    const themeGroup = value.find((item: SelectableItem) => item.id === 'theme') as SelectableGroupItem
    if (themeGroup) {
      themeGroup.children.forEach((item: SelectableSingleItem, index: number) => {
      if (item.selected)
        themeIdx.value = index
      })
    }
    // default values, while there are only the quercus_robur data
    const speciesGroup = value.find((item: SelectableItem) => item.id === 'species') as SelectableGroupItem
    if (speciesGroup) {
      // find the genre of the default species
      genre.value = speciesGroup.children.find((item) => item.selected)?.genre
    }
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
          v-model="genre"
          label="Genre"
          :items="genreItems"
          item-title="label"
          item-value="id"
          density="compact"
          class="mt-2"
        ></v-select>
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
