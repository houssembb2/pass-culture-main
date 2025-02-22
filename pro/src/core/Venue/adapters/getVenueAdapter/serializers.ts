import { BannerMetaModel, GetVenueResponseModel } from 'apiClient/v1'
import { IVenueBannerMetaProps } from 'components/pages/Offerers/Offerer/VenueV1/VenueEdition/ImageVenueUploaderSection/ImageVenueUploaderSection'
import { IVenue } from 'core/Venue'

export const serializeVenueApi = (venue: GetVenueResponseModel): IVenue => {
  return {
    bannerMeta: venue.bannerMeta
      ? serializeBannerMetaApi(venue.bannerMeta)
      : undefined,
    bannerUrl: venue.bannerUrl || '',
    comment: venue.comment || '',
    contact: {
      phoneNumber: venue.contact?.phoneNumber || '',
      email: venue.contact?.email || '',
      webSite: venue.contact?.website || '',
    },
    description: venue.description || '',
    id: venue.id,
    isPermanent: venue.isPermanent || false,
    isVenueVirtual: venue.isVirtual,
    mail: venue.bookingEmail || '',
    name: venue.name,
    publicName: venue.publicName || '',
    siret: venue.siret || '',
    venueLabel: venue.venueLabelId || '',
    venueType: venue.venueTypeCode || '',
  }
}

const serializeBannerMetaApi = (
  apiBannerMeta: BannerMetaModel
): IVenueBannerMetaProps => {
  return {
    image_credit: apiBannerMeta.image_credit || '',
    original_image_url: apiBannerMeta.original_image_url || '',
    crop_params: {
      x_crop_percent: apiBannerMeta.crop_params?.x_crop_percent || 0,
      y_crop_percent: apiBannerMeta.crop_params?.y_crop_percent || 0,
      width_crop_percent: apiBannerMeta.crop_params?.width_crop_percent || 0,
      height_crop_percent: apiBannerMeta.crop_params?.height_crop_percent || 0,
    },
  }
}
