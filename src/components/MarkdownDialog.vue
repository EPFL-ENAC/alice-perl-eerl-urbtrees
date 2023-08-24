<script setup lang="ts">
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useDisplay } from 'vuetify'
import { defineProps, onMounted, ref, withDefaults } from 'vue'

const props = withDefaults(
  defineProps<{
    name?: string;
    contentUrl: string
    width?: string;
    open?: boolean;
    buttonText?: string;
  }>(),
  {
    name: undefined,
    contentUrl: undefined,
    width: "unset",
    open: false,
    buttonText: undefined,
  }
)

const emit = defineEmits(['dialogClose'])

const dialog = ref<boolean>(false)
const { mobile } = useDisplay()
const contentHtml = ref<string>('')

onMounted(() => {
  if (props.open) {
    dialog.value = true;
  }
  axios
    .get<string>(props.contentUrl)
    .then((response) => response.data)
    .then((data) => {
      contentHtml.value = DOMPurify.sanitize(marked.parse(data, {headerIds: false, mangle: false}))
    })
})

function close() {
  dialog.value = false
  emit('dialogClose')
}
</script>

<template>
  <v-dialog v-model="dialog" :width="width" :fullscreen="mobile">
    <template #activator="{ on, attrs }">
      <slot name="activator" :on="on" :attrs="attrs" />
    </template>
    <v-card class="text-justify">
      <v-card-title v-if="name">{{ name }}</v-card-title>
      <v-card-text>
        <br v-if="!name" />
        <div v-html="contentHtml" class="marked"></div>
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn v-if="buttonText" text @click="close">
          {{ buttonText }}
        </v-btn>
        <v-btn v-else icon @click="close()">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
