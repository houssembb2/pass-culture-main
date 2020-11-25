from datetime import datetime
from datetime import timedelta
from unittest import mock
import urllib.parse

import pytest

from pcapi.core.bookings.factories import BookingFactory
import pcapi.core.bookings.models as bookings_models
import pcapi.core.offers.factories as offers_factories
from pcapi.core.payments.factories import PaymentFactory
from pcapi.core.users.factories import UserFactory
from pcapi.model_creators.generic_creators import create_booking
from pcapi.model_creators.generic_creators import create_deposit
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_user_offerer
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.specific_creators import create_event_occurrence
from pcapi.model_creators.specific_creators import create_offer_with_event_product
from pcapi.model_creators.specific_creators import create_offer_with_thing_product
from pcapi.model_creators.specific_creators import create_stock_from_event_occurrence
from pcapi.model_creators.specific_creators import create_stock_with_event_offer
from pcapi.models import Booking
from pcapi.models import Deposit
from pcapi.models import EventType
from pcapi.models import ThingType
from pcapi.models import UserSQLEntity
from pcapi.models import api_errors
from pcapi.repository import repository
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient


tomorrow = datetime.utcnow() + timedelta(days=1)
tomorrow_minus_one_hour = tomorrow - timedelta(hours=1)


@pytest.mark.usefixtures("db_session")
class Returns204:  # No Content
    def when_user_has_rights(self, app):
        booking = BookingFactory(token="ABCDEF")
        pro_user = UserFactory(email="pro@example.com")
        offerer = booking.stock.offer.venue.managingOfferer
        offers_factories.UserOffererFactory(user=pro_user, offerer=offerer)

        url = f"/bookings/token/{booking.token}"
        response = TestClient(app.test_client()).with_auth("pro@example.com").patch(url)

        assert response.status_code == 204
        booking = bookings_models.Booking.query.one()
        assert booking.isUsed
        assert booking.dateUsed is not None

    def when_header_is_not_standard_but_request_is_valid(self, app):
        booking = BookingFactory(token="ABCDEF")
        pro_user = UserFactory(email="pro@example.com")
        offerer = booking.stock.offer.venue.managingOfferer
        offers_factories.UserOffererFactory(user=pro_user, offerer=offerer)

        url = f"/bookings/token/{booking.token}"
        client = TestClient(app.test_client()).with_auth("pro@example.com")
        response = client.patch(url, headers={"origin": "http://random_header.fr"})

        assert response.status_code == 204
        booking = bookings_models.Booking.query.one()
        assert booking.isUsed

    # FIXME: what is the purpose of this test? Are we testing that
    # Flask knows how to URL-decode parameters?
    def when_booking_user_email_has_special_character_url_encoded(self, app):
        booking = BookingFactory(
            token="ABCDEF",
            user__email="user+plus@example.com",
        )
        pro_user = UserFactory(email="pro@example.com")
        offerer = booking.stock.offer.venue.managingOfferer
        offers_factories.UserOffererFactory(user=pro_user, offerer=offerer)

        quoted_email = urllib.parse.quote("user+plus@example.com")
        url = f"/bookings/token/{booking.token}?email={quoted_email}"
        client = TestClient(app.test_client()).with_auth("pro@example.com")
        response = client.patch(url, headers={"origin": "http://random_header.fr"})

        assert response.status_code == 204
        booking = bookings_models.Booking.query.one()
        assert booking.isUsed

    def when_user_patching_is_global_admin_is_activation_event_and_no_deposit_for_booking_user(self, app):
        # Given
        user = create_user(can_book_free_offers=False, is_admin=False, first_name="John")
        pro_user = create_user(can_book_free_offers=False, email="pro@email.fr", is_admin=True)
        offerer = create_offerer()
        user_offerer = create_user_offerer(pro_user, offerer)
        venue = create_venue(offerer)
        activation_offer = create_offer_with_event_product(venue, event_type=EventType.ACTIVATION)
        activation_event_occurrence = create_event_occurrence(activation_offer, beginning_datetime=tomorrow)
        stock = create_stock_from_event_occurrence(
            activation_event_occurrence, price=0, booking_limit_date=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)
        repository.save(booking, user_offerer)
        user_id = user.id
        url = "/bookings/token/{}".format(booking.token)

        # When
        response = TestClient(app.test_client()).with_auth("pro@email.fr").patch(url)

        # Then
        user = UserSQLEntity.query.get(user_id)
        assert response.status_code == 204
        assert user.canBookFreeOffers
        deposits_for_user = Deposit.query.filter_by(userId=user.id).all()
        assert len(deposits_for_user) == 1
        assert deposits_for_user[0].amount == 500
        assert user.canBookFreeOffers

    def when_user_patching_is_global_admin_is_activation_thing_and_no_deposit_for_booking_user(self, app):
        # Given
        user = create_user(can_book_free_offers=False, is_admin=False, first_name="John")
        pro_user = create_user(can_book_free_offers=False, email="pro@email.fr", is_admin=True)
        offerer = create_offerer()
        user_offerer = create_user_offerer(pro_user, offerer)
        venue = create_venue(offerer)
        activation_offer = create_offer_with_thing_product(venue, thing_type=ThingType.ACTIVATION)
        activation_event_occurrence = create_event_occurrence(activation_offer, beginning_datetime=tomorrow)
        stock = create_stock_from_event_occurrence(
            activation_event_occurrence, price=0, booking_limit_date=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)
        repository.save(booking, user_offerer)
        user_id = user.id
        url = "/bookings/token/{}".format(booking.token)

        # When
        response = TestClient(app.test_client()).with_auth("pro@email.fr").patch(url)

        # Then
        user = UserSQLEntity.query.get(user_id)
        assert response.status_code == 204
        assert user.canBookFreeOffers
        deposits_for_user = Deposit.query.filter_by(userId=user.id).all()
        assert len(deposits_for_user) == 1
        assert deposits_for_user[0].amount == 500
        assert user.canBookFreeOffers


class Returns403:
    @pytest.mark.usefixtures("db_session")
    def when_user_not_editor_and_valid_email(self, app):
        # Given
        user = create_user()
        admin_user = create_user(email="admin@email.fr")
        offerer = create_offerer()
        venue = create_venue(offerer)
        stock = create_stock_with_event_offer(
            offerer, venue, price=0, beginning_datetime=tomorrow, booking_limit_datetime=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)
        repository.save(booking, admin_user)
        booking_id = booking.id
        url = "/bookings/token/{}?email={}".format(booking.token, user.email)

        # When
        response = TestClient(app.test_client()).with_auth("admin@email.fr").patch(url)

        # Then
        assert response.status_code == 403
        assert response.json["global"] == [
            "Vous n'avez pas les droits d'accès suffisant pour accéder à cette information."
        ]
        assert not Booking.query.get(booking_id).isUsed

    @mock.patch("pcapi.core.bookings.validation.check_is_usable")
    @pytest.mark.usefixtures("db_session")
    def when_booking_not_confirmed(self, mocked_check_is_usable, app):
        # Given
        next_week = datetime.utcnow() + timedelta(weeks=1)
        booking = BookingFactory(stock__beginningDatetime=next_week)
        pro_user = UserFactory(email="pro@example.com")
        offerer = booking.stock.offer.venue.managingOfferer
        offers_factories.UserOffererFactory(user=pro_user, offerer=offerer)
        url = "/bookings/token/{}".format(booking.token)
        mocked_check_is_usable.side_effect = api_errors.ForbiddenError(errors={"booking": ["Not confirmed"]})

        # When
        response = TestClient(app.test_client()).with_auth("pro@example.com").patch(url)

        # Then
        assert response.status_code == 403
        assert response.json["booking"] == ["Not confirmed"]

    @pytest.mark.usefixtures("db_session")
    def when_it_is_an_offer_on_an_activation_event_and_user_patching_is_not_global_admin(self, app):
        # Given
        user = create_user()
        pro_user = create_user(email="pro@email.fr", is_admin=False)
        offerer = create_offerer()
        user_offerer = create_user_offerer(pro_user, offerer)
        venue = create_venue(offerer)
        activation_offer = create_offer_with_event_product(venue, event_type=EventType.ACTIVATION)
        activation_event_occurrence = create_event_occurrence(activation_offer)
        stock = create_stock_from_event_occurrence(activation_event_occurrence, price=0)
        activation_offer = create_offer_with_event_product(venue, event_type=EventType.ACTIVATION)
        activation_event_occurrence = create_event_occurrence(activation_offer, beginning_datetime=tomorrow)
        stock = create_stock_from_event_occurrence(
            activation_event_occurrence, price=0, booking_limit_date=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)
        repository.save(booking, user_offerer)
        url = "/bookings/token/{}".format(booking.token)

        # When
        response = TestClient(app.test_client()).with_auth("pro@email.fr").patch(url)

        # Then
        assert response.status_code == 403

    @pytest.mark.usefixtures("db_session")
    def when_booking_is_cancelled(self, app):
        # Given
        admin = UserFactory(isAdmin=True, canBookFreeOffers=False)
        booking = BookingFactory(isCancelled=True)
        url = f"/bookings/token/{booking.token}"

        # When
        response = TestClient(app.test_client()).with_auth(admin.email).patch(url)

        # Then
        assert response.status_code == 403
        assert response.json["booking"] == ["Cette réservation a été annulée"]
        assert not Booking.query.get(booking.id).isUsed

    @pytest.mark.usefixtures("db_session")
    def when_booking_is_refunded(self, app):
        # Given
        admin = UserFactory(isAdmin=True, canBookFreeOffers=False)
        booking = BookingFactory(isUsed=True)
        PaymentFactory(booking=booking)
        url = f"/bookings/token/{booking.token}"

        # When
        response = TestClient(app.test_client()).with_auth(admin.email).patch(url)

        # Then
        assert response.status_code == 403
        assert response.json["payment"] == ["Cette réservation a été remboursée"]


class Returns404:
    @pytest.mark.usefixtures("db_session")
    def when_user_not_editor_and_invalid_email(self, app):
        # Given
        user = create_user()
        admin_user = create_user(email="admin@email.fr")
        offerer = create_offerer()
        venue = create_venue(offerer)
        stock = create_stock_with_event_offer(
            offerer, venue, price=0, beginning_datetime=tomorrow, booking_limit_datetime=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)
        repository.save(booking, admin_user)
        booking_id = booking.id
        url = "/bookings/token/{}?email={}".format(booking.token, "wrong@email.fr")

        # When
        response = TestClient(app.test_client()).with_auth("admin@email.fr").patch(url)

        # Then
        assert response.status_code == 404
        assert not Booking.query.get(booking_id).isUsed

    @pytest.mark.usefixtures("db_session")
    def when_booking_user_email_with_special_character_not_url_encoded(self, app):
        # Given
        user = create_user(email="user+plus@email.fr")
        user_admin = create_user(email="admin@email.fr")
        offerer = create_offerer()
        user_offerer = create_user_offerer(user_admin, offerer, is_admin=True)
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, event_name="Event Name")
        event_occurrence = create_event_occurrence(offer, beginning_datetime=tomorrow)
        stock = create_stock_from_event_occurrence(
            event_occurrence, price=0, booking_limit_date=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)

        repository.save(user_offerer, booking)
        url = "/bookings/token/{}?email={}".format(booking.token, user.email)

        # When
        response = TestClient(app.test_client()).with_auth("admin@email.fr").patch(url)

        # Then
        assert response.status_code == 404

    @pytest.mark.usefixtures("db_session")
    def when_user_not_editor_and_valid_email_but_invalid_offer_id(self, app):
        # Given
        user = create_user()
        admin_user = create_user(email="admin@email.fr")
        offerer = create_offerer()
        venue = create_venue(offerer)
        stock = create_stock_with_event_offer(
            offerer, venue, price=0, beginning_datetime=tomorrow, booking_limit_datetime=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)
        repository.save(booking, admin_user)
        booking_id = booking.id
        url = "/bookings/token/{}?email={}&offer_id={}".format(booking.token, user.email, humanize(123))

        # When
        response = TestClient(app.test_client()).with_auth("admin@email.fr").patch(url)

        # Then
        assert response.status_code == 404
        assert not Booking.query.get(booking_id).isUsed


class Returns405:  # Method Not Allowed
    @pytest.mark.usefixtures("db_session")
    def when_user_patching_is_global_admin_is_activation_offer_and_existing_deposit_for_booking_user(self, app):
        # Given
        user = create_user(can_book_free_offers=False, is_admin=False)
        pro_user = create_user(can_book_free_offers=False, email="pro@email.fr", is_admin=True)
        offerer = create_offerer()
        user_offerer = create_user_offerer(pro_user, offerer)
        venue = create_venue(offerer)
        activation_offer = create_offer_with_event_product(venue, event_type=EventType.ACTIVATION)
        activation_event_occurrence = create_event_occurrence(activation_offer, beginning_datetime=tomorrow)
        stock = create_stock_from_event_occurrence(
            activation_event_occurrence, price=0, booking_limit_date=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)
        deposit = create_deposit(user, amount=500)
        repository.save(booking, user_offerer, deposit)
        user_id = user.id
        url = "/bookings/token/{}".format(booking.token)

        # When
        response = TestClient(app.test_client()).with_auth("pro@email.fr").patch(url)

        # Then
        deposits_for_user = Deposit.query.filter_by(userId=user_id).all()
        assert response.status_code == 405
        assert len(deposits_for_user) == 1
        assert deposits_for_user[0].amount == 500


class Returns410:  # Gone
    @pytest.mark.usefixtures("db_session")
    def when_booking_already_validated(self, app):
        # Given
        user = create_user()
        admin_user = create_user(email="admin@email.fr")
        offerer = create_offerer()
        user_offerer = create_user_offerer(admin_user, offerer)
        venue = create_venue(offerer)
        stock = create_stock_with_event_offer(
            offerer, venue, price=0, beginning_datetime=tomorrow, booking_limit_datetime=tomorrow_minus_one_hour
        )
        booking = create_booking(user=user, stock=stock, venue=venue)
        booking.isUsed = True
        repository.save(booking, user_offerer)
        booking_id = booking.id

        url = "/bookings/token/{}".format(booking.token)

        # When
        response = TestClient(app.test_client()).with_auth("admin@email.fr").patch(url)

        # Then
        assert response.status_code == 410
        assert response.json["booking"] == ["Cette réservation a déjà été validée"]
        assert Booking.query.get(booking_id).isUsed
