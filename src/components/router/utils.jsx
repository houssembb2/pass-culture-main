import { pipe } from '../../utils/functionnals'

export const removeHrefRoutes = routes =>
  routes.filter(route => !route.href)

export const removeDisabledRoutes = routes =>
  routes.filter(route => !route.disabled)

export const extendRoutesWithExact = routes =>
  routes.map(obj => {
    const exact = obj && obj.exact === undefined ? true : obj.exact
    const extend = { exact }
    return { ...obj, ...extend }
  })

export const addMenuViewToRoutesWithPath = routes =>
  routes.map(route => {
    const clone = { ...route }
    if (clone.path) {
      clone.path = `${clone.path}/:menu(menu)?`
    }
    return clone
  })

export const getBrowserRoutes = routes => pipe(
  addMenuViewToRoutesWithPath,
  removeHrefRoutes,
  removeDisabledRoutes,
  extendRoutesWithExact,
)(routes)
