import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'
import colors from 'vuetify/lib/util/colors'
import 'vuetify/styles'

// Translations provided by Vuetify
import { en, fr } from 'vuetify/locale'

export default createVuetify({
  locale: {
    locale: 'en',
    fallback: 'en',
    messages: { en, fr },
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi
    }
  },
  theme: {
    themes: {
      light: {
        colors: {
          primary: colors.shades.black,
          secondary: colors.blue.base
        }
      }
    }
  }
})
