<script setup lang="ts">
import { RouterView } from 'vue-router'
import epflLogoUrl from '/EPFL_Logo_184X53.svg'
import { mdiInformation } from '@mdi/js'
import { useI18n } from 'vue-i18n'
import { useLocale } from 'vuetify'
import { useCookies } from 'vue3-cookies'
import { ref } from 'vue'

const showHome = ref<boolean>(false)
const secret = ref<string>()

const { current } = useLocale()
const { locale } = useI18n({ useScope: 'global' })
const { cookies } = useCookies()

function onLocale(lang: string) {
  locale.value = lang
  current.value = lang
  cookies.set('locale', lang, '365d')
}

function getCurrentLocaleOrFallback() {
  return ['en', 'fr'].includes(current.value) ? current.value : 'en'
}

function onSecretChange() {
  if (secret.value === 'urbs2023') {
    showHome.value = true
  }
}
</script>

<template>
  <v-app>
    <v-app-bar flat height="68" v-if="showHome">
      <v-app-bar-title>
        <div class="text-h5">URBTREES</div>
        <div class="text-subtitle-2">{{ $t('app_subtitle') }}</div>
      </v-app-bar-title>

      <v-btn
        id="locales-activator"
        color="primary"
        class="mr-2"
      >
        {{ getCurrentLocaleOrFallback() }}
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
    <v-main v-if="showHome">
      <RouterView/>
    </v-main>
    <v-main v-else>
      <div>
        <v-row class="mt-16">
          <v-col cols="4">
          </v-col>
          <v-col cols="4">
            <v-text-field
              v-model="secret"
              label="Type secret and press Enter"
              hide-details="auto"
              type="password"
              @change="onSecretChange"
            ></v-text-field>
          </v-col>
          <v-col cols="4">
          </v-col>
        </v-row>
      </div>
    </v-main>
  </v-app>
</template>


<style lang="scss" scoped>
.v-app-bar {
  border-bottom: 1px solid rgb(var(--v-theme-primary));
}
</style>
