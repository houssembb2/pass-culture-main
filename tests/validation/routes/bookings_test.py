from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from domain.expenses import SUBVENTION_PHYSICAL_THINGS, SUBVENTION_DIGITAL_THINGS
from models import ApiErrors, Booking, Stock, Offer, ThingType, User, EventType
from models.api_errors import ResourceGoneError, ForbiddenError
from repository import repository
from tests.conftest import clean_database
from tests.model_creators.generic_creators import create_booking, create_user, create_stock, create_offerer, \
    create_venue, \
    create_user_offerer, create_payment, create_deposit
from tests.model_creators.specific_creators import create_booking_for_thing, create_stock_from_offer, \
    create_product_with_thing_type, create_product_with_event_type, create_offer_with_thing_product, \
    create_offer_with_event_product
from utils.human_ids import humanize
from validation.routes.bookings import check_expenses_limits, \
    check_booking_is_cancellable_by_user, \
    check_quantity_is_valid, \
    check_rights_to_get_bookings_csv, \
    check_booking_is_not_already_cancelled, \
    check_booking_is_not_used, \
    check_booking_token_is_usable, \
    check_booking_token_is_keepable, \
    check_is_not_activation_booking, check_stock_is_bookable, check_already_booked


class CheckExpenseLimitsTest:
    def test_raises_an_error_when_physical_limit_is_reached(self):
        # given
        expenses = {
            'physical': {'max': SUBVENTION_PHYSICAL_THINGS, 'actual': 190},
            'digital': {'max': SUBVENTION_DIGITAL_THINGS, 'actual': 10}
        }
        booking = Booking(from_dict={'stockId': humanize(123), 'amount': 11, 'quantity': 1})
        stock = create_booking_for_thing(product_type=ThingType.LIVRE_EDITION).stock

        # when
        with pytest.raises(ApiErrors) as api_errors:
            check_expenses_limits(expenses, booking, stock)

        # then
        assert api_errors.value.errors['global'] == ['Le plafond de %s € pour les biens culturels ne vous permet pas ' \
                                                     'de réserver cette offre.' % SUBVENTION_PHYSICAL_THINGS]

    def test_check_expenses_limits_raises_an_error_when_digital_limit_is_reached(self):
        # given
        expenses = {
            'physical': {'max': SUBVENTION_PHYSICAL_THINGS, 'actual': 10},
            'digital': {'max': SUBVENTION_DIGITAL_THINGS, 'actual': 190}
        }
        booking = Booking(from_dict={'stockId': humanize(123), 'amount': 11, 'quantity': 1})
        stock = create_booking_for_thing(url='http://on.line', product_type=ThingType.JEUX_VIDEO).stock

        # when
        with pytest.raises(ApiErrors) as api_errors:
            check_expenses_limits(expenses, booking, stock)

        # then
        assert api_errors.value.errors['global'] == ['Le plafond de %s € pour les offres numériques ne vous permet pas ' \
                                                     'de réserver cette offre.' % SUBVENTION_DIGITAL_THINGS]

    def test_does_not_raise_an_error_when_actual_expenses_are_lower_than_max(self):
        # given
        expenses = {
            'physical': {'max': SUBVENTION_PHYSICAL_THINGS, 'actual': 90},
            'digital': {'max': SUBVENTION_DIGITAL_THINGS, 'actual': 90}
        }
        booking = Booking(from_dict={'stockId': humanize(123), 'amount': 11, 'quantity': 1})
        stock = create_booking_for_thing(url='http://on.line', product_type=ThingType.JEUX_VIDEO).stock

        # when
        try:
            check_expenses_limits(expenses, booking, stock)
        except ApiErrors:
            # then
            pytest.fail('Booking for events must not raise any exceptions')


class CheckBookingIsCancellableTest:
    def test_raises_api_error_when_offerer_cancellation_and_used_booking(self):
        # Given
        booking = Booking()
        booking.isUsed = True

        # When
        with pytest.raises(ApiErrors) as e:
            check_booking_is_cancellable_by_user(booking, is_user_cancellation=False)

        # Then
        assert e.value.errors['booking'] == ["Impossible d\'annuler une réservation consommée"]

    def test_raises_api_error_when_user_cancellation_and_event_in_less_than_72h(self):
        # Given
        booking = Booking()
        booking.isUsed = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = datetime.utcnow() + timedelta(hours=71)

        # When
        with pytest.raises(ApiErrors) as e:
            check_booking_is_cancellable_by_user(booking, is_user_cancellation=True)

        # Then
        assert e.value.errors['booking'] == [
            "Impossible d\'annuler une réservation moins de 72h avant le début de l'évènement"]

    def test_does_not_raise_api_error_when_user_cancellation_and_event_in_more_than_72h(self):
        # Given
        booking = Booking()
        booking.isUsed = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = datetime.utcnow() + timedelta(hours=73)

        # When
        check_output = check_booking_is_cancellable_by_user(booking, is_user_cancellation=False)

        # Then
        assert check_output is None

    def test_does_not_raise_api_error_when_offerer_cancellation_and_event_in_less_than_72h(self):
        # Given
        booking = Booking()
        booking.isUsed = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = datetime.utcnow() + timedelta(hours=71)

        # When
        check_output = check_booking_is_cancellable_by_user(booking, is_user_cancellation=False)

        # Then
        assert check_output is None

    def test_does_not_raise_api_error_when_offerer_cancellation_not_used_and_thing(self):
        # Given
        booking = Booking()
        booking.isUsed = False
        booking.stock = Stock()
        booking.stock.offer = Offer()
        booking.stock.offer.product = create_product_with_thing_type()

        # When
        check_output = check_booking_is_cancellable_by_user(booking, is_user_cancellation=False)

        # Then
        assert check_output is None


class CheckBookingIsUsableTest:
    def test_raises_resource_gone_error_if_is_used(self):
        # Given
        booking = Booking()
        booking.isUsed = True
        booking.stock = Stock()

        # When
        with pytest.raises(ResourceGoneError) as e:
            check_booking_token_is_usable(booking)
        assert e.value.errors['booking'] == [
            'Cette réservation a déjà été validée']

    def test_raises_resource_gone_error_if_is_cancelled(self):
        # Given
        booking = Booking()
        booking.isUsed = False
        booking.isCancelled = True
        booking.stock = Stock()

        # When
        with pytest.raises(ResourceGoneError) as e:
            check_booking_token_is_usable(booking)
        assert e.value.errors['booking'] == [
            'Cette réservation a été annulée']

    def test_raises_resource_gone_error_if_stock_beginning_datetime_in_more_than_72_hours(self):
        # Given
        in_four_days = datetime.utcnow() + timedelta(days=4)
        booking = Booking()
        booking.isUsed = False
        booking.isCancelled = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = in_four_days

        # When
        with pytest.raises(ForbiddenError) as e:
            check_booking_token_is_usable(booking)
        assert e.value.errors['beginningDatetime'] == [
            'Vous ne pouvez pas valider cette contremarque plus de 72h avant le début de l\'évènement']

    def test_does_not_raise_error_if_not_cancelled_nor_used_and_no_beginning_datetime(self):
        # Given
        booking = Booking()
        booking.isUsed = False
        booking.isCancelled = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = None

        # When
        try:
            check_booking_token_is_usable(booking)
        except ApiErrors:
            pytest.fail(
                'Bookings which are not used nor cancelled and do not have a beginning datetime should be usable')

    def test_does_not_raise_error_if_not_cancelled_nor_used_and_beginning_datetime_in_less_than_72_hours(self):
        # Given
        in_two_days = datetime.utcnow() + timedelta(days=2)
        booking = Booking()
        booking.isUsed = False
        booking.isCancelled = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = in_two_days

        # When
        try:
            check_booking_token_is_usable(booking)
        except ApiErrors:
            pytest.fail(
                'Bookings which are not used nor cancelled and do not have a beginning datetime should be usable')


class CheckRightsToGetBookingsCsvTest:
    @clean_database
    def test_raises_an_error_when_user_is_admin(self, app):
        # given
        user_admin = create_user(can_book_free_offers=False, is_admin=True)

        repository.save(user_admin)

        # when
        with pytest.raises(ApiErrors) as e:
            check_rights_to_get_bookings_csv(user_admin)
        assert e.value.errors['global'] == [
            "Le statut d'administrateur ne permet pas d'accéder au suivi des réseravtions"]

    @clean_database
    def test_raises_an_error_when_user_has_no_right_on_venue_id(self, app):
        # given
        offerer1 = create_offerer(siren='123456789')
        user_with_rights_on_venue = create_user(email='test@example.net', is_admin=False)
        user_offerer1 = create_user_offerer(user_with_rights_on_venue, offerer1)

        user_with_no_rights_on_venue = create_user(is_admin=False)

        venue = create_venue(offerer1, siret=offerer1.siren + '12345')

        repository.save(user_offerer1, user_with_no_rights_on_venue, venue)

        # when
        with pytest.raises(ApiErrors) as e:
            check_rights_to_get_bookings_csv(user_with_no_rights_on_venue, venue_id=venue.id)
        assert e.value.errors['global'] == [
            'Vous n\'avez pas les droits d\'accès suffisant pour accéder à cette information.']

    @clean_database
    def test_raises_an_error_when_user_has_no_right_on_offer_id(self, app):
        # given
        user_with_no_rights_on_offer = create_user(email='pro_with_no_right@example.net', is_admin=False)

        offerer1 = create_offerer(siren='123456789')
        user_with_rights_on_offer = create_user(email='test@example.net', is_admin=False)
        user_offerer1 = create_user_offerer(user_with_rights_on_offer, offerer1)
        venue = create_venue(offerer1, siret=offerer1.siren + '12345')
        offer = create_offer_with_event_product(venue)

        repository.save(user_offerer1, user_with_no_rights_on_offer, venue)

        # when
        with pytest.raises(ApiErrors) as e:
            check_rights_to_get_bookings_csv(user_with_no_rights_on_offer, offer_id=offer.id)
        assert e.value.errors['global'] == [
            'Vous n\'avez pas les droits d\'accès suffisant pour accéder à cette information.']

    @clean_database
    def test_raises_an_error_when_venue_does_not_exist(self, app):
        # given
        user = create_user(email='pro_with_no_right@example.net', is_admin=False)

        repository.save(user)

        # when
        with pytest.raises(ApiErrors) as e:
            check_rights_to_get_bookings_csv(user, venue_id=-1)
        assert e.value.errors['venueId'] == ["Ce lieu n'existe pas."]

    @clean_database
    def test_raises_an_error_when_offer_does_not_exist(self, app):
        # given
        user = create_user(email='pro_with_no_right@example.net', is_admin=False)

        repository.save(user)

        # when
        with pytest.raises(ApiErrors) as e:
            check_rights_to_get_bookings_csv(user, offer_id=-1)
        assert e.value.errors['offerId'] == ["Cette offre n'existe pas."]


class CheckQuantityIsValidTest:
    @clean_database
    def test_raise_error_when_booking_quantity_is_None_or_zero(self, app):
        # given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_duo=False)
        stock = create_stock(offer=offer)
        repository.save(stock)
        quantity = 0

        # when
        with pytest.raises(ApiErrors) as api_errors:
            check_quantity_is_valid(quantity, stock)

        # then
        assert api_errors.value.errors['quantity'] == [
            "Vous devez réserver une place ou deux dans le cas d'une offre DUO."]

    @clean_database
    def test_raise_error_when_booking_quantity_is_bigger_than_one_and_offer_is_not_duo(self, app):
        # given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_duo=False)
        stock = create_stock(offer=offer)
        repository.save(stock)
        quantity = 2

        # when
        with pytest.raises(ApiErrors) as api_errors:
            check_quantity_is_valid(quantity, stock)

        # then
        assert api_errors.value.errors['quantity'] == [
            "Vous devez réserver une place ou deux dans le cas d'une offre DUO."]

    @clean_database
    def test_does_not_raise_an_error_when_booking_quantity_is_one_and_offer_is_not_duo(self, app):
        # given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_duo=False)
        stock = create_stock(offer=offer)
        repository.save(stock)
        quantity = 1

        # when
        try:
            check_quantity_is_valid(quantity, stock)
        except ApiErrors:
            # then
            pytest.fail('Booking for single offer must not raise any exceptions')

    @clean_database
    def test_raise_error_when_booking_quantity_is_more_than_two_and_offer_is_duo(self, app):
        # given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_duo=True)
        stock = create_stock(offer=offer)
        repository.save(stock)
        quantity = 3

        # when
        with pytest.raises(ApiErrors) as api_errors:
            check_quantity_is_valid(quantity, stock)

        # then
        assert api_errors.value.errors['quantity'] == [
            "Vous devez réserver une place ou deux dans le cas d'une offre DUO."]

    @clean_database
    def test_does_not_raise_an_error_when_booking_quantity_is_one_and_offer_is_duo(self, app):
        # given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_duo=True)
        stock = create_stock(offer=offer)
        repository.save(stock)
        quantity = 1

        # when
        try:
            check_quantity_is_valid(quantity, stock)
        except ApiErrors:
            # then
            pytest.fail('Booking for duo offers must not raise any exceptions')

    @clean_database
    def test_does_not_raise_an_error_when_booking_quantity_is_two_and_offer_is_duo(self, app):
        # given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_duo=True)
        stock = create_stock(offer=offer)
        repository.save(stock)
        quantity = 2

        # when
        try:
            check_quantity_is_valid(quantity, stock)
        except ApiErrors:
            # then
            pytest.fail('Booking for duo offers must not raise any exceptions')


class CheckBookingIsNotAlreadyCancelledTest:
    def test_raise_resource_gone_error_when_booking_is_already_cancelled(self):
        # Given
        user = create_user(postal_code=None)
        booking = create_booking(user=user, is_cancelled=True)

        # When
        with pytest.raises(ResourceGoneError) as api_errors:
            check_booking_is_not_already_cancelled(booking)

        # Then
        assert api_errors.value.errors['global'] == ["Cette contremarque a déjà été annulée"]

    def test_does_not_raise_when_the_booking_is_not_already_cancelled(self):
        # Given
        user = create_user(postal_code=None)
        booking = create_booking(user=user, is_cancelled=False)

        # When
        try:
            check_booking_is_not_already_cancelled(booking)
        except ResourceGoneError:
            # Then
            pytest.fail('Non cancelled booking should not raise errors')


class CheckBookingIsNotUsedTest:
    def test_raise_forbidden_error_when_booking_is_already_used(self):
        # Given
        user = create_user(postal_code=None)
        booking = create_booking(user=user, is_used=True)

        # When
        with pytest.raises(ForbiddenError) as api_errors:
            check_booking_is_not_used(booking)

        # Then
        assert api_errors.value.errors['global'] == ["Impossible d\'annuler une réservation consommée"]

    def test_does_not_raise_when_the_booking_is_not_used(self):
        # Given
        user = create_user(postal_code=None)
        booking = create_booking(user=user, is_used=False)

        # When
        try:
            check_booking_is_not_used(booking)
        except ResourceGoneError:
            # Then
            pytest.fail('Non used booking should pass the test')


class CheckActivationBookingCanBeKeptTest:
    def test_should_raise_an_error_when_booking_has_an_event_activation_type(self):
        # Given
        product = create_product_with_event_type(event_type=EventType.ACTIVATION)
        offer = create_offer_with_event_product(product=product)
        stock = create_stock(offer=offer)
        booking = create_booking(user=User(), stock=stock)

        # when
        with pytest.raises(ApiErrors) as api_errors:
            check_is_not_activation_booking(booking)

        # then
        assert api_errors.value.errors['booking'] == ["Impossible d'annuler une offre d'activation"]

    def test_should_raise_an_error_when_booking_has_a_thing_activation_type(self):
        # Given
        product = create_product_with_event_type(event_type=ThingType.ACTIVATION)
        offer = create_offer_with_event_product(product=product)
        stock = create_stock(offer=offer)
        booking = create_booking(user=User(), stock=stock)

        # when
        with pytest.raises(ApiErrors) as api_errors:
            check_is_not_activation_booking(booking)

        # then
        assert api_errors.value.errors['booking'] == ["Impossible d'annuler une offre d'activation"]

    def test_should_not_raise_when_booking_is_not_an_activation(self):
        # Given
        product = create_product_with_event_type(event_type=EventType.JEUX)
        offer = create_offer_with_event_product(product=product)
        stock = create_stock(offer=offer)
        booking = create_booking(user=User(), stock=stock)

        # when
        try:
            check_is_not_activation_booking(booking)
        except:
            assert False


class CheckBookingIsKeepableTest:
    def test_raises_resource_gone_error_if_not_used(self, app):
        # Given
        booking = Booking()
        booking.isUsed = False
        booking.stock = Stock()

        # When
        with pytest.raises(ResourceGoneError) as e:
            check_booking_token_is_keepable(booking)
        assert e.value.errors['booking'] == [
            "Cette réservation n'a encore été validée"]

    def test_raises_resource_gone_error_if_validated_and_cancelled(self, app):
        # Given
        booking = Booking()
        booking.isUsed = True
        booking.isCancelled = True
        booking.stock = Stock()

        # When
        with pytest.raises(ResourceGoneError) as e:
            check_booking_token_is_keepable(booking)
        assert e.value.errors['booking'] == [
            'Cette réservation a été annulée']

    @clean_database
    def test_raises_resource_gone_error_if_payement_exists(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, )
        stock = create_stock_from_offer(offer, price=0)

        booking = create_booking(user=user, stock=stock)

        payment = create_payment(booking, offerer, Decimal(10), iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        repository.save(payment)

        # When
        with pytest.raises(ResourceGoneError) as e:
            check_booking_token_is_keepable(booking)
        assert e.value.errors['payment'] == [
            'Le remboursement est en cours de traitement']

    def test_does_not_raise_error_if_stock_beginning_datetime_in_more_than_72_hours_after_validating(self, app):
        # Given
        in_four_days = datetime.utcnow() + timedelta(days=4)
        booking = Booking()
        booking.isUsed = True
        booking.isCancelled = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = in_four_days

        # When
        try:
            check_booking_token_is_keepable(booking)
        except ApiErrors:
            pytest.fail(
                'Bookings token which are used and not cancelled and  have a beginning datetime in more than 72 hours should be keepable')

    def test_does_not_raise_error_if_not_cancelled_but_used_and_no_beginning_datetime(self, app):
        # Given
        booking = Booking()
        booking.isUsed = True
        booking.isCancelled = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = None

        # When
        try:
            check_booking_token_is_keepable(booking)
        except ApiErrors:
            pytest.fail(
                'Bookings token which are used nor cancelled and do not have a beginning datetime should be keepable')

    def test_does_not_raise_error_if_neither_cancelled_but_used_and_beginning_datetime_in_less_than_72_hours(self, app):
        # Given
        in_two_days = datetime.utcnow() + timedelta(days=2)
        booking = Booking()
        booking.isUsed = True
        booking.isCancelled = False
        booking.stock = Stock()
        booking.stock.beginningDatetime = in_two_days

        # When
        try:
            check_booking_token_is_keepable(booking)
        except ApiErrors:
            pytest.fail(
                'Bookings token which are used and no cancelled and do not have a beginning datetime should be keepable')


class CheckStockIsBookableTest:
    def test_should_raise_error_when_stock_is_not_bookable(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=False)

        # When
        stock = create_stock(offer=offer)

        # When
        with pytest.raises(ApiErrors) as error:
            check_stock_is_bookable(stock)

        # Then
        assert error.value.errors == {'stock': ["Ce stock n'est pas réservable"]}


class CheckAlreadyBookedTest:
    @clean_database
    def test_should_not_raise_exception_when_user_has_never_book_a_stock(self, app):
        # Given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer)
        repository.save(user, stock)

        # When
        check_already_booked(stock, user)

        # Then
        assert True

    @clean_database
    def test_should_raise_exception_when_user_has_already_book(self, app):
        # Given
        user = create_user()
        create_deposit(user)
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer)
        booking = create_booking(user, stock=stock)
        repository.save(user, stock, booking)

        # When
        with pytest.raises(ApiErrors) as error:
            check_already_booked(stock, user)

        assert error.value.errors == {'stockId': ["Cette offre a déja été reservée par l'utilisateur"]}
