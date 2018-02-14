import React, { Component } from 'react'
import { connect } from 'react-redux'
import { compose } from 'redux'
import { createSelector } from 'reselect'

import OfferItem from '../components/OfferItem'
import withLogin from '../hocs/withLogin'
import { requestData } from '../reducers/data'

class OffersList extends Component {
  handleRequestData = props => {
    const { requestData, user } = props
    if (!this.hasRequired && user) {
      requestData('GET', 'offers')
      this.hasRequired = true
    }
  }
  componentWillMount () {
    this.props.user && this.handleRequestData(this.props)
  }
  componentWillReceiveProps (nextProps) {
    if (nextProps.user && nextProps.user !== this.props.user) {
      this.handleRequestData(nextProps)
    }
  }
  render () {
    const { offers } = this.props
    return (
      <div className='md-col-9 mx-auto'>
        {
          offers && offers.map((offer, index) => [
            <OfferItem isModify
              isPrices
              isFavorites
              key={index}
              {...offer}
            />,
            (index !== offers.length -1) && <div className='sep mb2' key={`sep-${index}`}/>
          ])
        }
      </div>
    )
  }
}

const getSortOffers = createSelector(state => state.data.offers,
  offers => {
    if (!offers) {
      return
    }
    const sortOffers = [...offers]
    // youngest are at the top of the list
    sortOffers.sort((o1, o2) => o2.id - o1.id)
    return sortOffers
  })

export default compose(
  withLogin,
  connect(
    state =>({
      offers: getSortOffers(state),
      user: state.user
    }),
    { requestData }
  )
)(OffersList)
