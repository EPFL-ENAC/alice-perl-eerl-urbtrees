export type SelectableItem = SelectableSingleItem | SelectableGroupItem
export interface SelectableParentItem {
  label: string
  selected?: boolean
}

export interface ScaleEntry {
  color: string
  label: string
  min?: number
  max?: number
  unit?: string
}

export interface SelectableSingleItem extends SelectableParentItem {
  id: string
  ids: string[]
  genre: string
  legend?: string
  legendImage?: string
  legendScaleId?: string
}
export interface SelectableGroupItem extends SelectableParentItem {
  id: string
  tab: boolean
  children: SelectableSingleItem[]
}

export interface SpeciesItem {
  GENRE_lat: string
  GENRE_fr: string
  GENRE_eng: string
  'GENUS TREE COUNT': number
  'GENUS SHARE': string
  NOM_COMPLET_lat: string
  NOM_COMPLET_fr: string
  NOM_COMPLET_eng: string
  'SPECIE TREE COUNT': number
  'SPECIE SHARE': string
  sum_BVOC_kg: number
  mean_BVOC_kg: number
  sum_O3_kg: number
  mean_O3_kg: number
  sum_OFP_kg: number
  mean_OFP_kg: number
  sum_PM10_kg: number
  mean_PM10_kg: number
  Net_O3: number
}