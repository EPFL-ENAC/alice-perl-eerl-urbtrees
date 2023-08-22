<script setup lang="ts">
import 'maplibre-gl/dist/maplibre-gl.css'
import '@maplibre/maplibre-gl-geocoder/dist/maplibre-gl-geocoder.css'

import { geocoderApi } from '@/utils/geocoder'
import { DivControl } from '@/utils/control'
import type { LegendScale, ScaleEntry } from '@/utils/jsonWebMap'
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

defineExpose({
  update
})
const props = withDefaults(
  defineProps<{
    styleSpec: string | StyleSpecification
    center?: LngLatLike
    zoom?: number
    scales: LegendScale[]
    aspectRatio?: number
    minZoom?: number
    maxZoom?: number
    selectableLayerIds?: string[]
    selectedLayerIds?: string[]
    popupLayerIds?: string[]
    areaLayerIds?: string[]
  }>(),
  {
    center: undefined,
    zoom: 12,
    scales: () => [],
    aspectRatio: undefined,
    minZoom: undefined,
    maxZoom: undefined,
    selectableLayerIds: () => [],
    selectedLayerIds: () => [],
    popupLayerIds: () => [],
    areaLayerIds: () => []
  }
)

const loading = ref(true)
let map: Map | undefined = undefined

onMounted(() => {
  map = new Map({
    container: 'maplibre-map',
    style: props.styleSpec,
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
      compact: true,
      customAttribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>, <a href="https://www.epfl.ch/labs/perl/" target="_blank">PERL</a>, <a href="https://www.epfl.ch/labs/alice/" target="_blank">ALICE</a>, <a href="https://www.epfl.ch/labs/eerl/" target="_blank">EERL</a>'
  }));
  map.addControl(
    new MaplibreGeocoder(geocoderApi, {
      maplibregl: { Marker },
      showResultsWhileTyping: true,
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
    map?.setStyle(styleSpec)
  },
  { immediate: true }
)
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
          const fprops = e.features?.at(0)?.properties
          // display tree attributes
          if (fprops) {
            const rows = Object.keys(fprops).map((key) => `<tr><th>${key}</th><td>${fprops[key]}</td></tr>`)
            let html = `<p class="text-overline">${layerId}</p>
              <table>
                ${rows.join('\n')}
              </table>`
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
      .forEach((layer) => {
        map?.setLayoutProperty(
          layer.id,
          'visibility',
          props.selectedLayerIds.includes(layer.id) ? 'visible' : 'none'
        )
      })
  }
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
