import { connect } from 'react-redux'

import { selectCurrentUser } from 'store/user/selectors'

import { SetPasswordConfirm } from './SetPasswordConfirm'

export const mapStateToProps = state => {
  return {
    currentUser: selectCurrentUser(state),
  }
}

export default connect(mapStateToProps)(SetPasswordConfirm)
