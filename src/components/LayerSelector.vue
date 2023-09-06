<script setup lang="ts">
import type { LegendScale } from '@/utils/jsonWebMap'
import type { SelectableItem, SelectableGroupItem, SelectableSingleItem, SpeciesItem } from '@/utils/layerSelector'
import { watch, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = withDefaults(
  defineProps<{
    modelValue?: string[]
    items?: SelectableItem[],
    scales?: LegendScale[],
    species: SpeciesItem[]
  }>(),
  {
    modelValue: () => [],
    items: () => [],
    scales: () => []
  }
)
const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>()

const { t, locale } = useI18n({ useScope: 'global' })

const genre = ref<string>()
const genreItems = computed<{ id: string; label: string }[]>(() => {
  const key = `GENRE_${locale.value === 'en' ? 'eng' : locale.value}`
  return props.species
    .filter((value, index, array) => array.map((g) => g.GENRE_lat).indexOf(value.GENRE_lat) === index)
    .map((g) => { return { id: g.GENRE_lat.toLowerCase().replace(' ', '_'), label: `${(g as any)[key]} (${g.GENRE_lat})` }})
    .sort(itemCompare)
})

const tab = ref<string>()
const selectableTabs = computed<SelectableItem[]>(() =>
  props.items?.filter((item: SelectableItem) => (item as SelectableGroupItem).tab)
    .flatMap((item: SelectableItem) => (item as SelectableGroupItem).children)
    .filter((item: SelectableSingleItem) => item.genre === genre.value) // filter species by selected genre
)
const selectedTab = computed<SelectableSingleItem | undefined>(() =>
  selectableTabs.value.find((item) => item.id === tab.value) as SelectableSingleItem
)
const tabItems = computed<{ id: string; label: string }[]>(() => selectableTabs.value.map((item) => {
  const label = (item as any)[`label_${locale.value}`]
  return {
    id: item.id,
    label: `${label} (${item.label})`
  }
}).sort(itemCompare))

const scale = ref<string>()
const scaleItems = computed<any[]>(() => props.scales?.
  filter((scl) => selectedTab.value && selectedTab.value.measures.includes(scl.id))
  .map((scl) => {
    return {
      id: scl.id,
      title: t(scl.id)
    }
  }))

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

watch(scale, () => {
  updateLayers()
})

watch(() => props.items,
  (value: SelectableItem[]) => {
    // init with declared species
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
    if (value && value.length>0) {
      scale.value = value[0].id
    }
    updateLayers()
  },
  { immediate: true }
)

function itemCompare(a: { id: string; label: string }, b: { id: string; label: string }) {
  if (a.label < b.label) {
    return -1
  }
  if (a.label > b.label) {
    return 1
  }
  return 0
}

function updateLayers() {
  const sels = []
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
      <div class="mt-2">
        <v-select
          v-model="genre"
          :label="$t('genus')"
          :items="genreItems"
          item-title="label"
          item-value="id"
          density="compact"
          class="mt-2"
        ></v-select>
        <v-select
          v-model="tab"
          :label="$t('specie')"
          :items="tabItems"
          item-title="label"
          item-value="id"
          density="compact"
          class="mt-2"
        ></v-select>
        <v-select
          v-model="scale"
          :label="$t('measure')"
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
