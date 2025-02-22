import { ACCESSIBILITY_DEFAULT_VALUES } from './Accessibility'
import { CATEGORIES_DEFAULT_VALUES } from './Categories'
import { INFORMATIONS_DEFAULT_VALUES } from './Informations'
import { NOTIFICATIONS_DEFAULT_VALUES } from './Notifications'
import { USEFUL_INFORMATIONS_DEFAULT_VALUES } from './UsefulInformations'

export const FORM_DEFAULT_VALUES = {
  ...INFORMATIONS_DEFAULT_VALUES,
  ...CATEGORIES_DEFAULT_VALUES,
  ...USEFUL_INFORMATIONS_DEFAULT_VALUES,
  ...ACCESSIBILITY_DEFAULT_VALUES,
  ...NOTIFICATIONS_DEFAULT_VALUES,
}
