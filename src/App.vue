<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { RouterView } from 'vue-router'
import { useTitleStore } from './stores/title'
import epflLogoUrl from '/EPFL_Logo_184X53.svg'
import { mdiInformation } from '@mdi/js'
import { useI18n } from 'vue-i18n'

const { title, subtitle } = storeToRefs(useTitleStore())
const { locale } = useI18n({ useScope: 'global' })

function onLocale(lang: string) {
  locale.value = lang
}
</script>

<template>
  <v-app>
    <v-app-bar flat height="68">
      <v-app-bar-title>
        <div v-if="title" class="text-h5">{{ title }}</div>
        <div v-if="subtitle" class="text-subtitle-2">{{ $t(subtitle) }}</div>
      </v-app-bar-title>

      <v-btn
        id="locales-activator"
        color="primary"
        class="mr-2"
      >
        {{ locale }}
      </v-btn>

    <v-menu activator="#locales-activator">
      <v-list>
        <v-list-item
          v-for="(lang, index) in $i18n.availableLocales"
          :key="index"
        >
          <v-list-item-title @click="onLocale(lang)">{{ $t(lang) }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
      <v-btn to="/about" :icon="mdiInformation" class="mr-3"></v-btn>
      <template #append>
        <a href="https://epfl.ch" target="_blank">
          <v-img :src="epflLogoUrl" width="100px" />
        </a>
      </template>
    </v-app-bar>
    <v-main>
      <RouterView />
    </v-main>
  </v-app>
</template>

<style lang="scss" scoped>
.v-app-bar {
  border-bottom: 1px solid rgb(var(--v-theme-primary));
}
</style>
