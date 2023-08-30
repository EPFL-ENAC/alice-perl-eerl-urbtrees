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
import { useI18n } from 'vue-i18n'
import type { StyleSpecification } from 'maplibre-gl'
// @ts-ignore
import Papa from 'papaparse'

const props = defineProps<{
  styleUrl: string
  parametersUrl: string
  cdnUrl: string
}>()

const CDN_DATA_URL = `${props.cdnUrl}/data`

const { t, locale } = useI18n({ useScope: 'global' })

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
              // normalize locales
              row.GENRE_en = row.GENRE_eng
              row.NOM_COMPLET_en = row.NOM_COMPLET_eng
              if (row.mean_BVOC_kg) {
                row.measures.push('voc')
              }
              if (row.mean_PM10_kg) {
                row.measures.push('pm10')
              }
              if (row.mean_O3_kg) {
                row.measures.push('o3')
              }
              if (row.mean_OFP_kg) {
                row.measures.push('ofp')
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
              label_en: item.NOM_COMPLET_en,
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
const selectedItemWithLegend = computed(() =>
  singleItems.value
    .filter((item: SelectableSingleItem) => selectedLayerIds.value.some((id: string) => item.id === id))
    .filter((item: SelectableSingleItem) => item.legend !== undefined || item.legendImage !== undefined || item.legendScaleId !== undefined)
    .pop()
)
const selectedSpecie = computed(() => getSpecie(selectedItemWithLegend.value))

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

function getSpecie(sel: SelectableSingleItem | undefined) {
  return sel ? species.value.filter((item) => item.id === sel.id).pop() : undefined
}

function onOpenLegendDialog(item: SelectableSingleItem) {
  const label = (item as any)['label_' + locale.value]
  legendDialogTitle.value = `${item.label} (${label})`
  legendDialogImageSrc.value = item.legendImage
  legendDialog.value = true
}

function getLegendTitle(id: string, withUnit: boolean): string | undefined {
  const scale = parameters.value?.legendScales?.find((scale: LegendScale) => scale.id === id)
  if (scale) { 
    if (withUnit && scale.unit) {
      return `${t(scale.id)} (${t(scale.unit)})`
    }
    return t(scale.id)
  }
  return undefined
}

function getLegendScale(id: string): ScaleEntry[] | undefined {
  return parameters.value?.legendScales?.find((scale: LegendScale) => scale.id === id)?.scale
}

function getLegendScaleEntryCaption(entry: ScaleEntry): string {
  let rval = ''
  if (entry.range)
    rval = `${formatNumber(entry.range[0])} - ${formatNumber(entry.range[1])}`
  if (entry.unit)
    rval = `${rval} ${entry.unit }`
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

function formatNumber(nb: number) {
  return new Intl.NumberFormat(`${locale.value}`).format(nb)
}

function getGenusTreeCountLabel(sel: SpeciesItem) {
  return formatNumber(sel['GENUS TREE COUNT'])
}

function getGenusShareLabel(sel: SpeciesItem) {
  return formatNumber(Number.parseFloat(sel['GENUS SHARE'].replace('%', ''))) + '%'
}

function getSpecieTreeCountLabel(sel: SpeciesItem) {
  return formatNumber(sel['SPECIE TREE COUNT'])
}

function getSpecieShareLabel(sel: SpeciesItem) {
  return formatNumber(Number.parseFloat(sel['SPECIE SHARE'].replace('%', ''))) + '%'
}

function isMeasurePositive(measure: string) {
  return ['voc', 'ofp'].includes(measure)
}

function getSpecieMeasureMeanLabel(sel: SpeciesItem, measure: string) {
  const field = `mean_${measure === 'voc' ? 'BVOC' : measure.toUpperCase()}_kg`
  const val = formatNumber((sel as any)[field])
  const sign = isMeasurePositive(measure) ? '+' : '-'
  return `${sign}${val}`
}

function getSpecieMeasureSumLabel(sel: SpeciesItem, measure: string) {
  const field = `sum_${measure === 'voc' ? 'BVOC' : measure.toUpperCase()}_kg`
  const val = formatNumber((sel as any)[field])
  const sign = isMeasurePositive(measure) ? '+' : '-'
  return `${sign}${val}`
}

function getSpecieGenusLabel(sel: SpeciesItem) {
  const label = (sel as any)[`GENRE_${locale.value}`]
  return `${sel.GENRE_lat} (${label})`
}

function getSpecieLabel(sel: SpeciesItem) {
  const label = (sel as any)[`NOM_COMPLET_${locale.value}`]
  return `${sel.NOM_COMPLET_lat} (${label})`
}

</script>

<template>
  <v-navigation-drawer :rail="drawerRail" permanent :width="mobile ? 200 : 400" @click="drawerRail = false">
    <v-list density="compact" nav>
      <v-list-item :prepend-icon="drawerRail ? mdiChevronRight : undefined">
        <template #append>
          <v-btn :icon="mdiChevronLeft" variant="flat" @click.stop="drawerRail = true" />
        </template>
      </v-list-item>
      <v-list-item :prepend-icon="mdiLayers">
        <v-list-item-title>
          <span class="text-h6">{{ $t('layers') }}</span>
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
      <v-list-item v-if="selectedItemWithLegend" :prepend-icon="mdiMapLegend">
        <v-list-item-title>
          <span class="text-h6">{{ $t('legends') }}</span>
        </v-list-item-title>
      </v-list-item>
      <v-list-item v-if="!drawerRail && selectedItemWithLegend && selectedSpecie">
        <v-card>
          <v-card-text class="pa-0">
            <v-row>
              <v-col cols="12">
                <div class="mb-2 text-overline">{{ getSpecieGenusLabel(selectedSpecie) }}</div>
                <v-row class="mb-1">
                  <v-col cols="6">
                    <v-chip size="x-large">
                      {{ $t('trees_count', { count: getGenusTreeCountLabel(selectedSpecie) }) }}
                    </v-chip>
                  </v-col>
                  <v-col cols="6">
                    <v-chip size="x-large">
                      {{ getGenusShareLabel(selectedSpecie) }}
                    </v-chip>
                  </v-col>
                </v-row>
                <div class="mb-5 text-caption text-grey-darken-1">{{ $t('share_genus') }}</div>

                <div class="mb-2 text-overline">{{ getSpecieLabel(selectedSpecie) }}</div>
                <v-row class="mb-1">
                  <v-col cols="6">
                    <v-chip size="x-large">
                      {{ $t('trees_count', { count: getSpecieTreeCountLabel(selectedSpecie) }) }}
                    </v-chip>
                  </v-col>
                  <v-col cols="6">
                    <v-chip size="x-large">
                      {{ getSpecieShareLabel(selectedSpecie) }}
                    </v-chip>
                  </v-col>
                </v-row>
                <div class="mb-3 text-caption text-grey-darken-1">{{ $t('share_specie') }}</div>
                
                <v-table density="compact" class="mb-2">
                  <thead>
                    <tr>
                      <th></th>
                      <th>{{ $t('mean') }}</th>
                      <th>{{ $t('sum') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <template v-for="measure in selectedSpecie.measures" :key="measure">
                      <tr>
                        <td class="text-caption">{{ getLegendTitle(measure, false) }}</td>
                        <td class="text-no-wrap" :class="isMeasurePositive(measure) ? 'text-red' : 'text-green'">
                          {{ getSpecieMeasureMeanLabel(selectedSpecie, measure) }} kg
                        </td>
                        <td class="text-no-wrap" :class="isMeasurePositive(measure) ? 'text-red' : 'text-green'">
                          {{ getSpecieMeasureSumLabel(selectedSpecie, measure) }} kg
                        </td>
                      </tr>
                    </template>
                  </tbody>
                </v-table>
                <div class="mb-5 text-caption text-grey-darken-1">{{ $t('annual_contrib') }}</div>

                <div v-if="selectedItemWithLegend.legend" class="mb-5 text-caption">{{ selectedItemWithLegend.legend }}</div>
                <div v-if="selectedItemWithLegend.legendImage" class="mb-5">
                  <v-hover v-slot="{ isHovering, props }">
                    <v-card
                      elevation="0"
                      class="v-card-image mb-2"
                      :class="{ 'on-hover': isHovering }"
                      v-bind="props"
                    >
                    <v-img :src="selectedItemWithLegend.legendImage" @click="onOpenLegendDialog(selectedItemWithLegend)">
                      <v-card-title class="d-flex justify-center align-self-auto" primary-title>
                          <v-btn
                            color="primary"
                            class="mt-4"
                            :prepend-icon="mdiOpenInNew"
                            style="z-index: 9999"
                            @click.stop="onOpenLegendDialog(selectedItemWithLegend)">
                            {{ $t('open') }}
                          </v-btn>
                      </v-card-title>
                    </v-img>
                    </v-card>
                  </v-hover>
                  <div class="text-caption text-grey-darken-1">{{ $t('o3_balance') }}</div>
                </div>

                <div v-if="scale" class="mb-3 text-overline">{{ getLegendTitle(scale, true) }}</div>
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
.v-card-image:not(.on-hover) {
  opacity: 0.6;
}
</style>
