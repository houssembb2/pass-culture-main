import { useFormikContext } from 'formik'
import React from 'react'

import FormLayout from 'new_components/FormLayout'
import { SubmitButton } from 'ui-kit'

import { Contact } from './Contact'
import ImageUploader from './ImageUploader/ImageUploader'
import { Informations } from './Informations'

import { IVenueFormValues } from '.'

interface IVenueForm {
  isCreatingVenue: boolean
  updateIsSiretValued: (isSiretValued: boolean) => void
  venueTypes: SelectOption[]
  venueLabels: SelectOption[]
}

const VenueForm = ({
  isCreatingVenue,
  updateIsSiretValued,
  venueTypes,
  venueLabels,
}: IVenueForm) => {
  const { isSubmitting, initialValues } = useFormikContext<IVenueFormValues>()
  const shouldDisplayImageVenueUploaderSection = initialValues?.isPermanent

  return (
    <div>
      <FormLayout>
        <Informations
          isCreatedEntity={isCreatingVenue}
          readOnly={!isCreatingVenue}
          updateIsSiretValued={updateIsSiretValued}
          venueIsVirtual={false}
          venueTypes={venueTypes}
          venueLabels={venueLabels}
        />
        {!!shouldDisplayImageVenueUploaderSection && (
          <ImageUploader {...initialValues} />
        )}
        <Contact />
        <SubmitButton isLoading={isSubmitting}>Valider</SubmitButton>
      </FormLayout>
    </div>
  )
}

export default VenueForm
