<script setup lang="ts">
import LayerSelector from '@/components/LayerSelector.vue'
import MapLibreMap from '@/components/MapLibreMap.vue'
import { useTitleStore } from '@/stores/title'
import type { Parameters, LegendScale, ScaleEntry } from '@/utils/jsonWebMap'
import { mdiChevronLeft, mdiChevronRight, mdiClose, mdiLayers, mdiMapLegend, mdiBookOpenPageVariant } from '@mdi/js'
import type { SelectableGroupItem, SelectableItem, SelectableSingleItem } from '@/utils/layerSelector'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { storeToRefs } from 'pinia'
import { useDisplay } from 'vuetify'
import { computed, onMounted, ref, shallowRef, triggerRef, watch } from 'vue'

const props = defineProps<{
  styleUrl: string
  parametersUrl: string
}>()

const map = ref<InstanceType<typeof MapLibreMap>>()
const selectedLayerIds = ref<string[]>([])
const parameters = shallowRef<Parameters>({})
const drawerRail = ref(false)
const drawerRight = ref(false)
const drawerHtml = ref('')
const docId = ref<string>()
const docHtml = ref<any>({})
const { mobile } = useDisplay()
const { title, subtitle } = storeToRefs(useTitleStore())

const documentationIds = [
  'trees'
]

onMounted(() => {
  documentationIds.forEach((id: string) => {
    axios
    .get<string>(`${id}.md`)
    .then((response) => response.data)
    .then((data) => {
      docHtml.value[id] = DOMPurify.sanitize(marked.parse(data, {headerIds: false}))
    })
  })
});

const singleItems = computed<SelectableSingleItem[]>(() =>
  (parameters.value.selectableItems ?? []).flatMap((item: SelectableItem) =>
    'children' in item ? item.children : [item]
  )
)
const selectableLayerIds = computed<string[]>(() => singleItems.value.map((item) => item.id))
const legendItems = computed(() =>
  singleItems.value
    .filter((item: SelectableSingleItem) => selectedLayerIds.value.some((id: string) => item.id === id))
    .filter((item: SelectableSingleItem) => item.legend !== undefined || item.legendImage !== undefined || item.legendScaleId !== undefined)
)

const extendedSelectedLayerIds = computed<string[]>(() => {
  const addtionalIds: string[] = singleItems.value
    .filter((item: SelectableSingleItem) => item.ids && selectedLayerIds.value.includes(item.id))
    .flatMap((item: SelectableSingleItem) => item.ids)
  const ids: string[] = [selectedLayerIds.value, addtionalIds].flat().filter((value, index, array) => array.indexOf(value) === index)
  return ids
})

watch(
  () => props.parametersUrl,
  (parametersUrl: string) => {
    axios
      .get<Parameters>(parametersUrl)
      .then((response) => response.data)
      .then((data) => {
        parameters.value = data
        triggerRef(parameters)
        map.value?.update(data.center, data.zoom)
        title.value = data.title
        subtitle.value = data.subtitle
        if (data.title) {
          document.title = data.title
        }
      })
  },
  { immediate: true }
)

function getParent(id: string): SelectableItem | undefined {
  return (parameters.value.selectableItems ?? [])
    .find((item: SelectableItem) => (item as SelectableGroupItem).children 
      && (item as SelectableGroupItem).children.find((child: SelectableSingleItem) => child.id == id) !== undefined)
}

function getParentLabel(id: string) {
  const parent = getParent(id)
  return parent?.label
}

function getLegendTitle(id: string): string | undefined {
  return parameters.value?.legendScales?.find((scale: LegendScale) => scale.id === id)?.title
}

function getLegendScale(id: string): ScaleEntry[] | undefined {
  return parameters.value?.legendScales?.find((scale: LegendScale) => scale.id === id)?.scale
}

function showDocumentation(id: string) {
  if (docId.value === id) {
    drawerRight.value = !drawerRight.value
  } else {
    if (id in docHtml.value) {
      drawerHtml.value = docHtml.value[id]
    } else {
      drawerHtml.value = `Ooops, no documentation about '${id}'`
    }
    docId.value = id
    drawerRight.value = true
  }
}

</script>

<template>
  <v-navigation-drawer :rail="drawerRail" permanent :width="mobile ? 200 : 300" @click="drawerRail = false">
    <v-list density="compact" nav>
      <v-list-item :prepend-icon="drawerRail ? mdiChevronRight : undefined">
        <template #append>
          <v-btn :icon="mdiChevronLeft" variant="flat" @click.stop="drawerRail = true" />
        </template>
      </v-list-item>
      <v-list-item :prepend-icon="mdiLayers">
        <v-list-item-title>
          <span class="text-h6">Layers</span>
        </v-list-item-title>
      </v-list-item>
      <v-list-item v-show="!drawerRail">
        <LayerSelector
          v-model="selectedLayerIds"
          :items="parameters.selectableItems"
        />
      </v-list-item>
      <v-list-item :prepend-icon="mdiMapLegend">
        <v-list-item-title>
          <span class="text-h6">Legend</span>
        </v-list-item-title>
      </v-list-item>
      <v-list-item v-if="!drawerRail">
        <v-card>
          <v-card-text class="pa-0">
            <v-row>
              <v-col v-for="(item, index) in legendItems" :key="index" cols="12">
                <div class="mb-2 text-overline">{{ getParentLabel(item.id) }} ({{ item.label }})</div>
                <div v-if="item.legend" class="mb-3 text-caption">{{ item.legend }}</div>
                <div v-if="item.legendScaleId" class="mb-3 text-caption">{{ getLegendTitle(item.legendScaleId) }}</div>
                <v-img v-if="item.legendImage" :src="item.legendImage" />
                <v-table v-if="item.legendScaleId" density="compact">
                  <tbody>
                    <tr
                      v-for="entry in getLegendScale(item.legendScaleId)"
                      :key="entry.color"
                    >
                      <td :style="`background-color: ${entry.color}`"></td>
                      <td>
                        <div>{{ entry.label }}</div>
                        <div class="text-caption">
                          <span v-if="entry.range">{{ entry.range[0] }} - {{ entry.range[1] }}</span>
                          <span v-if="entry.min === undefined && entry.max !== undefined">{{ entry.max }} &le;</span>
                          <span v-if="entry.min !== undefined && entry.max !== undefined">{{ entry.min }} - {{ entry.max }}</span>
                          <span v-if="entry.min !== undefined && entry.max === undefined">&gt; {{ entry.min }}</span>
                          <span v-if="entry.unit">&nbsp;({{ entry.unit }})</span>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-list-item>
      <v-list-item :prepend-icon="mdiBookOpenPageVariant">
        <v-list-item-title>
          <span class="text-h6">Documentation</span>
        </v-list-item-title>
      </v-list-item>
      <v-list-item v-if="!drawerRail">
        <div>
          <v-btn variant="text" class="text-none" @click="showDocumentation('trees')">Trees</v-btn>
        </div>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>
  <v-navigation-drawer v-if="drawerRight" permanent location="right" :width="mobile ? 400 : 800">
    <v-list>
      <v-list-item>
        <template #append>
          <v-btn :icon="mdiClose" variant="flat" @click.stop="drawerRight = false" />
        </template>
      </v-list-item>
      <v-list-item>
        <v-card>
          <v-card-text v-html="drawerHtml" class="marked">
          </v-card-text>
        </v-card>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>
  <v-container class="fill-height pa-0" fluid>
    <v-row class="fill-height">
      <v-col cols="12" class="py-0">
        <MapLibreMap
          ref="map"
          :center="parameters.center"
          :style-spec="styleUrl"
          :selectable-layer-ids="selectableLayerIds"
          :selected-layer-ids="extendedSelectedLayerIds"
          :popup-layer-ids="parameters.popupLayerIds"
          :zoom="parameters.zoom"
          :scales="parameters.legendScales"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<style lang="scss">
.v-navigation-drawer {
  border-right: 1px solid rgb(var(--v-theme-primary)) !important;
}
</style>
