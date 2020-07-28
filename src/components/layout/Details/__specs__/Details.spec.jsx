import { shallow } from 'enzyme'
import React from 'react'

import RectoContainer from '../../Recto/RectoContainer'
import VersoContainer from '../../Verso/VersoContainer'
import Details from '../Details'

describe('src | components | Details', () => {
  let props

  beforeEach(() => {
    props = {
      getOfferById: jest.fn(),
      match: {
        params: {},
      },
    }
  })

  describe('when I have no details', () => {
    it('should render VersoContainer and not RectoContainer', () => {
      // when
      const wrapper = shallow(<Details {...props} />)

      // then
      const versoContainer = wrapper.find(VersoContainer)
      expect(versoContainer).toHaveLength(1)
      const rectoContainer = wrapper.find(RectoContainer)
      expect(rectoContainer).toHaveLength(0)
    })
  })

  describe('when I have details', () => {
    it('should render VersoContainer and RectoContainer', () => {
      // given
      props.match.params.details = 'details'

      // when
      const wrapper = shallow(<Details {...props} />)
      wrapper.setState({ isDetailsView: true })

      // then
      const versoContainer = wrapper.find(VersoContainer)
      expect(versoContainer).toHaveLength(1)
      const rectoContainer = wrapper.find(RectoContainer)
      expect(rectoContainer).toHaveLength(1)
    })

    it('should fetch offers', () => {
      // given
      props.match = {
        params: {
          offerId: 'AE',
        },
      }

      // when
      shallow(<Details {...props} />)

      // then
      expect(props.getOfferById).toHaveBeenCalledWith('AE')
    })
  })
})
