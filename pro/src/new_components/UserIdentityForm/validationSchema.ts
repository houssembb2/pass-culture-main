import * as yup from 'yup'

const validationSchema = yup.object().shape({
  firstName: yup
    .string()
    .trim()
    .max(128)
    .required('Veuillez renseigner votre prénom'),
  lastName: yup
    .string()
    .trim()
    .max(128)
    .required('Veuillez renseigner votre nom'),
})

export default validationSchema
