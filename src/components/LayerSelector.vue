<script setup lang="ts">
import type { LegendScale } from '@/utils/jsonWebMap'
import type { SelectableItem, SelectableGroupItem, SelectableSingleItem, SpeciesItem } from '@/utils/layerSelector'
import { watch, ref, computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string[]
    items?: SelectableItem[],
    species: SpeciesItem[],
    scales: LegendScale[]
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
    .filter((value, index, array) => array.map((g) => g.GENRE_lat).indexOf(value.GENRE_lat) === index)
    .map((g) => { return { id: g.GENRE_lat.toLowerCase().replace(' ', '_'), label: `${g.GENRE_lat} (${g.GENRE_eng})` }})
)

const tab = ref<string>()
const selectableTabs = computed<SelectableItem[]>(() =>
  props.items?.filter((item: SelectableItem) => (item as SelectableGroupItem).tab)
    .flatMap((item: SelectableItem) => (item as SelectableGroupItem).children)
    .filter((item: SelectableSingleItem) => item.genre === genre.value) // filter species by selected genre
)
const selectedTab = computed<SelectableSingleItem | undefined>(() =>
  selectableTabs.value.find((item) => item.id === tab.value) as SelectableSingleItem
)
const tabItems = computed(() => selectableTabs.value.map((item) => {
  return {
    id: item.id,
    label: `${item.label} (${item.label_en})`
  }
}))

const scale = ref<string>()
const scaleItems = computed<LegendScale[]>(() => props.scales?.filter((scl) => selectedTab.value && selectedTab.value.measures.includes(scl.id)))

watch(genre, () => {
  // select the default species or the first one
  const selected = selectableTabs.value.find((item: SelectableItem) => item.selected)
  tab.value = selected ? selected.id : selectableTabs.value[0].id
})

watch(tab, () => {
  if (scaleItems.value && scaleItems.value.length > 0) {
    // keep current scale selection if it is valid or set the first one
    const selectedScale = scaleItems.value.find((scl) => scl.id === scale.value)
    if (selectedScale) {
      scale.value = selectedScale.id
    } else {
      scale.value = scaleItems.value[0].id
    }
  } else {
    scale.value = undefined
  }
  updateLayers()
})

watch([themeIdx, scale], () => {
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

watch(() => props.scales,
  (value: LegendScale[]) => {
    if (value) {
      scale.value = value[0].id
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
    const map = selectableTabs.value.filter((item: SelectableItem) => item.id === tab.value).pop()
    if (map) {
      sels.push(map.id)
      if (scale.value) {
        sels.push(`${map.id}_${scale.value}`)
      }
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
          label="Genus"
          :items="genreItems"
          item-title="label"
          item-value="id"
          density="compact"
          class="mt-2"
        ></v-select>
        <v-select
          v-model="tab"
          label="Specie"
          :items="tabItems"
          item-title="label"
          item-value="id"
          density="compact"
          class="mt-2"
        ></v-select>
        <v-select
          v-model="scale"
          label="Measure"
          :items="scaleItems"
          item-title="title"
          item-value="id"
          density="compact"
          class="mt-2"
        ></v-select>
      </div>

    </v-card-text>
  </v-card>
</template>
