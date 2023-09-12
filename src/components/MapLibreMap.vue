<script setup lang="ts">
import 'maplibre-gl/dist/maplibre-gl.css'
import '@maplibre/maplibre-gl-geocoder/dist/maplibre-gl-geocoder.css'
import 'maplibregl-theme-switcher/styles.css'
import 'maplibregl-scale-legend/styles.css'

import { geocoderApi } from '@/utils/geocoder'
import { DivControl } from '@/utils/control'
import { ThemeSwitcherControl } from 'maplibregl-theme-switcher'
import type { ThemeDefinition } from 'maplibregl-theme-switcher'
import { ScaleLegendControl } from 'maplibregl-scale-legend'
import type { ScaleDefinition } from 'maplibregl-scale-legend'
import MaplibreGeocoder from '@maplibre/maplibre-gl-geocoder'
import {
  AttributionControl,
  FullscreenControl,
  GeolocateControl,
  Map,
  MapMouseEvent,
  Marker,
  NavigationControl,
  Popup,
  ScaleControl,
  type LngLatLike,
  type StyleSpecification
} from 'maplibre-gl'
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { SelectableSingleItem, SpeciesProps } from '@/utils/layerSelector'
import type { LegendScale, ScaleEntry } from '@/utils/jsonWebMap'

defineExpose({
  update
})
const props = withDefaults(
  defineProps<{
    styleSpec: string | StyleSpecification | undefined
    center?: LngLatLike
    zoom?: number
    aspectRatio?: number
    minZoom?: number
    maxZoom?: number
    themes: SelectableSingleItem[]
    scales: LegendScale[]
    selectedScaleId?: string
    selectableLayerIds?: string[]
    selectedLayerIds?: string[]
    popupLayerIds?: string[]
    areaLayerIds?: string[]
  }>(),
  {
    center: undefined,
    zoom: 12,
    aspectRatio: undefined,
    minZoom: undefined,
    maxZoom: undefined,
    selectableLayerIds: () => [],
    selectedLayerIds: () => [],
    popupLayerIds: () => [],
    areaLayerIds: () => [],
    scales: () => [],
    selectedScaleId: undefined,
  }
)

const { t, locale } = useI18n({ useScope: 'global' })

const loading = ref(true)
let map: Map | undefined = undefined
const scaleControl = ref<ScaleLegendControl>()

onMounted(() => {
  map = new Map({
    container: 'maplibre-map',
    style: props.styleSpec || '',
    center: props.center,
    zoom: props.zoom,
    trackResize: true,
    attributionControl: false
  })
  map.addControl(new NavigationControl({}))
  map.addControl(new GeolocateControl({}))
  map.addControl(new ScaleControl({}))
  map.addControl(new FullscreenControl({}))
  map.addControl(new AttributionControl({
      compact: false,
      customAttribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>, <a href="https://www.swisstopo.admin.ch/fr/geodata/images/ortho.html" target="_blank">SWISSIMAGE</a>, <a href="https://www.epfl.ch/labs/perl/" target="_blank">PERL</a>, <a href="https://www.epfl.ch/labs/alice/" target="_blank">ALICE</a>, <a href="https://www.epfl.ch/labs/eerl/" target="_blank">EERL</a>'
  }));
  map.addControl(
    new MaplibreGeocoder(geocoderApi, {
      maplibregl: { Marker },
      showResultsWhileTyping: true,
      language: locale.value
    }),
    'top-left'
  )
  const positionControl = new DivControl({ id: 'map-position' })
  map.addControl(positionControl, 'bottom-left')
 

  map.on('mousemove', function (event: MapMouseEvent) {
    if (positionControl.container) {
      positionControl.container.innerHTML = `Lat/Lon: (${event.lngLat.lat.toFixed(4)}; ${event.lngLat.lng.toFixed(4)})`
    }
  })
  map.on('mouseout', function () {
    if (positionControl.container) {
      positionControl.container.innerHTML = ''
    }
  })

  map.once('load', () => {
    filterLayers()
    loading.value = false
  })
})

watch(
  () => props.styleSpec,
  (styleSpec) => {
    if (styleSpec) {
      map?.setStyle(styleSpec)
    }
  },
  { immediate: true }
)

watch(
  () => props.themes,
  (themes) => {
    if (themes) {
      const themeDefs: ThemeDefinition[] = themes.map((item: SelectableSingleItem) => {
        return {
          id: item.id,
          label: t(item.label),
          selected: item.selected
        }
      })
      const selectedTheme = themes.find((item) => item.selected)?.id
      map?.addControl(new ThemeSwitcherControl(themeDefs, selectedTheme))
    }
  },
  { immediate: true }
)


watch(
  () => props.scales,
  (scales) => {
    if (scales) {
      const scaleDefs: ScaleDefinition[] = scales.map((item: LegendScale) => {
        return {
          id: item.id,
          title: t(item.id),
          titleStart: item.titleStart ? t(item.titleStart) : undefined,
          titleEnd: item.titleEnd ? t(item.titleEnd) : undefined,
          scale: item.scale.map((entry: ScaleEntry) => {
            const range: string[] | undefined = entry.range ? [
                formatNumber(entry.range[0], "") ?? "",
                formatNumber(entry.range[1], "") ?? ""
              ] : undefined
            return {
              label: entry.label ? t(entry.label) : undefined,
              color: entry.color,
              range: range,
              unit: entry.unit ? t(entry.unit) : (item.unit ? t(item.unit) : undefined)
            }
          })
        }
      })
      scaleControl.value = new ScaleLegendControl(scaleDefs)
      map?.addControl(scaleControl.value, 'top-left')
      if (props.selectedScaleId) {
        scaleControl.value.showScale(props.selectedScaleId)
      }
    }
  },
  { immediate: true }
)

watch(() => props.selectedScaleId, () => {
  if (scaleControl.value) {
    scaleControl.value.showScale(props.selectedScaleId)
  }
}, {
  immediate: true
})

watch(
  () => props.popupLayerIds,
  (popupLayerIds) => {
    popupLayerIds.forEach((layerId) => {
      const popup = new Popup({
        closeButton: false,
        closeOnClick: true
      })
      map?.on('click', layerId, function (e) {
        if (map) {
          map.getCanvas().style.cursor = 'pointer'
          const fprops = e.features?.at(0)?.properties as SpeciesProps
          // display tree attributes
          if (fprops) {
            let label = locale.value === 'en' ? fprops.NOM_COMPLET_eng : (fprops as any)[`NOM_COMPLET_${locale.value}`]
            if (!label) {
              label = locale.value === 'en' ? fprops.GENRE_eng : (fprops as any)[`GENRE_${locale.value}`] 
            }
            let labelLat = fprops.NOM_COMPLET_lat
            if (!labelLat) {
              labelLat = fprops.GENRE_lat
            }
            let html = `
              <div class="marked">
              <p class="text-overline">${label} (${labelLat})</p>
              <table>
                <tbody>
                <tr>
                  <td class="text-caption font-weight-bold text-left pl-1 pr-0">${t('municipality')}</td>
                  <td class="text-no-wrap pl-1 pr-1">${fprops.COMMUNE}</td>
                </tr>
                <tr>
                  <td class="text-caption font-weight-bold text-left pl-1 pr-0">${t('leaf_type')}</td>
                  <td class="text-no-wrap pl-1 pr-1">${t(fprops.leaf)}</td>
                </tr>
                <tr>
                  <td class="text-caption font-weight-bold text-left pl-1 pr-0">${t('leaf_area')}</td>
                  <td class="text-no-wrap pl-1 pr-1">${formatNumber(fprops.L_area, t('m2'))}</td>
                </tr>
                <tr>
                  <td class="text-caption font-weight-bold text-left pl-1 pr-1">${t('voc')}</td>
                  <td class="text-no-wrap pl-1 pr-1">${formatNumber(fprops.VOC_g_y / 1000, t('kg/year')) ?? "-"}</td>
                </tr>
                <tr>
                  <td class="text-caption font-weight-bold text-left pl-1 pr-1">${t('pm10')}</td>
                  <td class="text-no-wrap pl-1 pr-1">${formatNumber(fprops.PM10_rm_gy / 1000, t('kg/year')) ?? "-"}</td>
                </tr>
                <tr>
                  <td class="text-caption font-weight-bold text-left pl-1 pr-1">${t('ofp')}</td>
                  <td class="text-no-wrap pl-1 pr-1">${formatNumber(fprops.OFP_kg_y, t('kg/year')) ?? "-"}</td>
                </tr>
                <tr>
                  <td class="text-caption font-weight-bold text-left pl-1 pr-1">${t('o3')}</td>
                  <td class="text-no-wrap pl-1 pr-1">${formatNumber(fprops.O3_rm_gy / 1000, t('kg/year')) ?? "-"}</td>
                </tr>
                </tbody>
              </table>
              </div>
              `
            popup
              .setLngLat(e.lngLat)
              .setHTML(html)
              .addTo(map)
          }
        }
      })
    })
  },
  { immediate: true }
)
watch([() => props.selectableLayerIds, () => props.selectedLayerIds], () => filterLayers(), {
  immediate: true
})

function update(center?: LngLatLike, zoom?: number) {
  if (map) {
    if (center !== undefined) {
      map.setCenter(center)
    }
    if (zoom !== undefined) {
      map.setZoom(zoom)
    }
  }
}

function filterLayers() {
  if (map?.loaded()) {
    map
      .getStyle()
      .layers
      .filter((layer) => !props.themes.map((theme) => theme.id).includes(layer.id))
      .forEach((layer) => {
        map?.setLayoutProperty(
          layer.id,
          'visibility',
          props.selectedLayerIds.includes(layer.id) ? 'visible' : 'none'
        )
      })
  }
}

function formatNumber(nb: number, unit: string) {
  
  return nb === undefined || isNaN(nb) ? undefined : `${new Intl.NumberFormat(`${locale.value}`).format(Math.round(nb * 100) / 100)} ${unit}`
}

</script>

<template>
  <v-progress-linear v-if="loading" active color="primary" indeterminate />
  <v-responsive :aspect-ratio="aspectRatio" height="100%">
    <div id="maplibre-map" />
  </v-responsive>
</template>

<style scoped>
#maplibre-map {
  height: 100%;
}
</style>
