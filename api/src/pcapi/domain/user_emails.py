from datetime import timedelta
import logging
import typing

from pcapi.core import mails
from pcapi.core.bookings.models import IndividualBooking
from pcapi.core.offerers.models import Offerer
from pcapi.core.offerers.repository import find_new_offerer_user_email
from pcapi.core.users import api as users_api
from pcapi.core.users.models import User
from pcapi.emails import beneficiary_activation
from pcapi.emails.new_offerer_validated_withdrawal_terms import (
    retrieve_data_for_new_offerer_validated_withdrawal_terms_email,
)
from pcapi.emails.offerer_booking_recap import retrieve_data_for_offerer_booking_recap_email


logger = logging.getLogger(__name__)


def send_individual_booking_confirmation_email_to_offerer(individual_booking: IndividualBooking) -> bool:
    offerer_booking_email = individual_booking.booking.stock.offer.bookingEmail
    if not offerer_booking_email:
        return True
    data = retrieve_data_for_offerer_booking_recap_email(individual_booking)
    return mails.send(recipients=[offerer_booking_email], data=data)


def send_activation_email(user: User, reset_password_token_life_time: typing.Optional[timedelta] = None) -> bool:
    token = users_api.create_reset_password_token(user, token_life_time=reset_password_token_life_time)
    data = beneficiary_activation.get_activation_email_data(user=user, token=token)

    return mails.send(recipients=[user.email], data=data)


def send_withdrawal_terms_to_newly_validated_offerer(offerer: Offerer) -> bool:
    offerer_email = find_new_offerer_user_email(offerer.id)
    data = retrieve_data_for_new_offerer_validated_withdrawal_terms_email()
    return mails.send(recipients=[offerer_email], data=data)


def send_dms_application_emails(users: typing.Iterable[User]) -> bool:
    data = beneficiary_activation.get_dms_application_data()
    return mails.send(recipients=[user.email for user in users], data=data)
