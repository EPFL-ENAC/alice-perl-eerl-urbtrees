<script setup lang="ts">
import LayerSelector from '@/components/LayerSelector.vue'
import MapLibreMap from '@/components/MapLibreMap.vue'
import { useTitleStore } from '@/stores/title'
import type { Parameters, LegendScale, ScaleEntry } from '@/utils/jsonWebMap'
import { mdiChevronLeft, mdiChevronRight, mdiClose, mdiLayers, mdiMapLegend, mdiBookOpenPageVariant, mdiOpenInNew } from '@mdi/js'
import type { SelectableGroupItem, SelectableItem, SelectableSingleItem, SpeciesItem } from '@/utils/layerSelector'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { storeToRefs } from 'pinia'
import { useDisplay } from 'vuetify'
import { computed, onMounted, ref, shallowRef, triggerRef, watch } from 'vue'
import type { StyleSpecification } from 'maplibre-gl'
// @ts-ignore
import Papa from 'papaparse'

const props = defineProps<{
  styleUrl: string
  parametersUrl: string
  cdnUrl: string
}>()

const CDN_DATA_URL = `${props.cdnUrl}/data`

const map = ref<InstanceType<typeof MapLibreMap>>()
const selectedLayerIds = ref<string[]>([])
const style = shallowRef<StyleSpecification>()
const parameters = shallowRef<Parameters>()
const legendDialog = ref(false)
const legendDialogTitle = ref<string>()
const legendDialogImageSrc = ref<string>()
const drawerRail = ref(false)
const drawerRight = ref(false)
const drawerHtml = ref('')
const docId = ref<string>()
const docHtml = ref<any>({})
const { mobile } = useDisplay()
const { title, subtitle } = storeToRefs(useTitleStore())

const documentationIds: string[] = [] // TODO not available for now

const species = ref<SpeciesItem[]>([])

onMounted(() => {
  documentationIds.forEach((id: string) => {
    axios
    .get<string>(`${id}.md`)
    .then((response) => response.data)
    .then((data) => {
      docHtml.value[id] = DOMPurify.sanitize(marked.parse(data, {headerIds: false, mangle: false}))
    })
  })

  axios
    .get(`${CDN_DATA_URL}/urbtrees_species_mean_sum_full.csv`)
    .then((response) => response.data)
    .then((data) => {
      Papa.parse(data, {
        delimiter: ',',
        header: true,
        dynamicTyping: true,
        complete: function(results: any) {
          species.value = results.data
            .filter((row: SpeciesItem) => row['GENRE_lat'] !== null)
            .map((row: SpeciesItem) => {
              row.id = row.NOM_COMPLET_lat.toLowerCase().replace(' ', '_')
              row.genus = row.GENRE_lat.toLowerCase().replace(' ', '_')
              row.measures = []
              if (row.mean_BVOC_kg) {
                row.measures.push('voc')
              }
              if (row.mean_O3_kg) {
                row.measures.push('o3')
              }
              if (row.mean_OFP_kg) {
                row.measures.push('ofp')
              }
              if (row.mean_PM10_kg) {
                row.measures.push('pm10')
              }
              return row
            })
        }
      })
    })  
});

watch(species, () => {
  axios
    .get<StyleSpecification>(props.styleUrl)
    .then((response) => response.data)
    .then((data) => {
      // append source/layer for each species read from the csv
      species.value.forEach((item) => {
        // one source for each specie
        data.sources[item.id] = {
          type: 'geojson',
          data: `${CDN_DATA_URL}/${item.id}.geojson`
        }
        // folliage layers
        item.measures.forEach((measure) => {
          data.layers.push({
            id: `${item.id}_${measure}`,
            source: item.id,
            type: 'circle',
            paint: {
              'circle-radius': [
                'interpolate',
                ['linear'],
                ['zoom'],
                13, 2,
                // @ts-ignore
                14, ['*', 0.125, ['number', ['get', 'radius'], 5]],
                // @ts-ignore
                15, ['*', 0.25, ['number', ['get', 'radius'], 5]],
                // @ts-ignore
                16, ['*', 0.5, ['number', ['get', 'radius'], 5]],
                // @ts-ignore
                17, ['number', ['get', 'radius'], 5],
                // @ts-ignore
                18, ['*', 2, ['number', ['get', 'radius'], 5]],
                // @ts-ignore
                19, ['*', 4, ['number', ['get', 'radius'], 5]]
              ],
              'circle-color': ['string', ['get', `color_${measure}`], '#000000'],
              'circle-opacity': [
                'case',
                ['==', '#000000', ['get', `color_${measure}`]], 0,
                0.7
              ],
              'circle-stroke-color': '#888888',
              'circle-stroke-width': 1,
              'circle-stroke-opacity': 0.3
            },
            layout: { visibility: 'none' }
          })
        })
        // crown layer
        data.layers.push({
          id: item.id,
          source: item.id,
          type: 'circle',
          paint: {
            'circle-radius': [
              'interpolate',
              ['linear'],
              ['zoom'],
              14, 1,
              // @ts-ignore
              15, ['*', 0.125, ['number', ['get', 'D_COUR_M'], 5]],
              // @ts-ignore
              16, ['*', 0.25, ['number', ['get', 'D_COUR_M'], 5]],
              // @ts-ignore
              17, ['*', 0.5, ['number', ['get', 'D_COUR_M'], 5]],
              // @ts-ignore
              18, ['number', ['get', 'D_COUR_M'], 5],
              // @ts-ignore
              19, ['*', 2, ['number', ['get', 'D_COUR_M'], 5]]
            ],
            'circle-color': '#aaaaaa',
            'circle-opacity': 0.3,
            'circle-stroke-color': '#888888',
            'circle-stroke-width': 1,
            'circle-stroke-opacity': 0.3
          },
          layout: { visibility: 'none' }
        })
      })
      style.value = data
    })
    .then(() => {
      axios
        .get<Parameters>(props.parametersUrl)
        .then((response) => response.data)
        .then((data) => {
          // append selectable for each species read from the csv
          const speciesItem = data.selectableItems?.find((item) => item.id === 'species') as SelectableGroupItem
          // find the most frequent specie and set it as the default one
          const maxCount = Math.max(...species.value.map((item) => item['SPECIE TREE COUNT']))
          const mostFrequentSpecies = species.value.find((item) => item['SPECIE TREE COUNT'] === maxCount)?.NOM_COMPLET_lat.toLowerCase().replace(' ', '_')
          species.value.forEach((item) => {
            speciesItem.children.push({
              id: item.id,
              ids: [item.id],
              label: item.NOM_COMPLET_lat,
              label_en: item.NOM_COMPLET_eng,
              label_fr: item.NOM_COMPLET_fr,
              legendImage: `${CDN_DATA_URL}/specie_${item.id}_graph.png`,
              measures: item.measures,
              genre: item.genus,
              selected: item.id === mostFrequentSpecies // most common, default one
            })
            data.popupLayerIds?.push(item.id)
            item.measures.forEach((measure) => data.popupLayerIds?.push(`${item.id}_${measure}`))
          })
          parameters.value = data
          triggerRef(parameters)
          triggerRef(style)
          map.value?.update(data.center, data.zoom)
          title.value = data.title
          subtitle.value = data.subtitle
          if (data.title) {
            document.title = data.title
          }
        })
    })
})

const singleItems = computed<SelectableSingleItem[]>(() =>
  (parameters.value?.selectableItems ?? [])
    .filter((item: SelectableItem) => item.id !== 'theme')
    .flatMap((item: SelectableItem) =>
      'children' in item ? item.children : [item]
    )
)

const themeItems = computed<SelectableSingleItem[]>(() => {
  const themeGroup = parameters.value?.selectableItems?.find((item: SelectableItem) => item.id === 'theme') as SelectableGroupItem
  return themeGroup ? themeGroup.children : []
})

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

const scale = computed<string | undefined>(() => {
  const scaleIds: string[] | undefined = parameters.value?.legendScales.map((scl) => scl.id)
  return selectedLayerIds.value.map((id) => id.split('_').pop()).filter((scl) => scl && scaleIds?.includes(scl)).pop()
})

function onOpenLegendDialog(item: SelectableSingleItem) {
  legendDialogTitle.value = `${item.label} (${item.label_en})`
  legendDialogImageSrc.value = item.legendImage
  legendDialog.value = true
}

function getLegendTitle(id: string): string | undefined {
  const scale = parameters.value?.legendScales?.find((scale: LegendScale) => scale.id === id)
  if (scale) { 
    if (scale.unit) {
      return `${scale.title} (${scale.unit})`
    }
    return scale.title
  }
  return undefined
}

function getLegendScale(id: string): ScaleEntry[] | undefined {
  return parameters.value?.legendScales?.find((scale: LegendScale) => scale.id === id)?.scale
}

function getLegendScaleEntryCaption(entry: ScaleEntry): string {
  let rval = ''
  if (entry.range)
    rval = `${entry.range[0]} - ${entry.range[1]}`
  if (entry.min === undefined && entry.max !== undefined)
    rval = `${entry.max} <=`
  if (entry.min !== undefined && entry.max !== undefined)
    rval = `${entry.min} - ${entry.max}`
  if (entry.min !== undefined && entry.max === undefined)
    rval = `> ${entry.min}`
  if (entry.unit)
    rval = `${rval} (${entry.unit })`
  return rval
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
  <v-navigation-drawer :rail="drawerRail" permanent :width="mobile ? 200 : 350" @click="drawerRail = false">
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
          :items="parameters?.selectableItems"
          :species="species"
          :scales="parameters?.legendScales"
        />
      </v-list-item>
      <v-list-item v-if="legendItems.length" :prepend-icon="mdiMapLegend">
        <v-list-item-title>
          <span class="text-h6">Legend</span>
        </v-list-item-title>
      </v-list-item>
      <v-list-item v-if="!drawerRail && legendItems.length">
        <v-card>
          <v-card-text class="pa-0">
            <v-row>
              <v-col v-for="(item, index) in legendItems" :key="index" cols="12">
                <div class="mb-2 text-overline">{{ item.label }} ({{ item.label_en }})</div>
                <div v-if="item.legend" class="mb-3 text-caption">{{ item.legend }}</div>
                
                <div v-if="item.legendImage" class="mb-3">
                  <v-btn
                    :icon="mdiOpenInNew"
                    size="xsmall"
                    flat
                    @click="onOpenLegendDialog(item)"
                  >
                  </v-btn>
                  <v-img :src="item.legendImage" @click="onOpenLegendDialog(item)"/>
                </div>
                <div v-if="scale" class="mb-3 text-caption font-weight-bold">{{ getLegendTitle(scale) }}</div>
                <v-table v-if="scale" density="compact">
                  <tbody>
                    <tr
                      v-for="entry in getLegendScale(scale)"
                      :key="entry.color"
                    >
                      <td :style="`background-color: ${entry.color}`"></td>
                      <td>
                        <div>{{ entry.label }}</div>
                        <div class="text-caption">
                          {{ getLegendScaleEntryCaption(entry) }}
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
      <v-list-item v-if="documentationIds.length>0" :prepend-icon="mdiBookOpenPageVariant">
        <v-list-item-title>
          <span class="text-h6">Documentation</span>
        </v-list-item-title>
      </v-list-item>
      <v-list-item v-if="documentationIds.length>0 && !drawerRail">
        <div v-for="doc of documentationIds" :key="doc">
          <v-btn variant="text" class="text-none" @click="showDocumentation(doc)">{{ doc }}</v-btn>
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
          :center="parameters?.center"
          :zoom="parameters?.zoom"
          :style-spec="style"
          :themes="themeItems"
          :selectable-layer-ids="selectableLayerIds"
          :selected-layer-ids="extendedSelectedLayerIds"
          :popup-layer-ids="parameters?.popupLayerIds"
        />
      </v-col>
    </v-row>

    <v-dialog
      v-model="legendDialog"
      fullscreen
    >
      <v-card>
        <v-toolbar
          color="grey-lighten-4"
        >
          <v-btn
            :icon="mdiClose"
            @click="legendDialog = false"
          >
          </v-btn>
          <v-toolbar-title>
            {{ legendDialogTitle }}
          </v-toolbar-title>
        </v-toolbar>
        <v-card-text>
          <v-img :src="legendDialogImageSrc"/>
        </v-card-text>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<style lang="scss">
.v-navigation-drawer {
  border-right: 1px solid rgb(var(--v-theme-primary)) !important;
}
</style>
