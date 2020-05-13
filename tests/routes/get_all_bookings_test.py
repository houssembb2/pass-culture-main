from datetime import datetime
from unittest.mock import patch

from repository import repository
from tests.conftest import clean_database, TestClient
from tests.model_creators.generic_creators import create_user, create_offerer, create_user_offerer, create_venue, \
    create_stock, create_booking
from tests.model_creators.specific_creators import create_offer_with_thing_product


class GetAllBookingsTest:
    @patch('routes.bookings.get_all_bookings_by_pro_user')
    @clean_database
    def test_should_call_the_usecase_method_get_all_bookings_by_pro_user(self,
                                                                         get_all_bookings_by_pro_user,
                                                                         app):
        # Given
        user = create_user(is_admin=True, can_book_free_offers=False)
        repository.save(user)

        # When
        TestClient(app.test_client()) \
            .with_auth(user.email) \
            .get('/bookings/pro')

        # Then
        get_all_bookings_by_pro_user.assert_called_once_with(user.id)


class GetTest:
    class Returns200Test:
        @clean_database
        def when_user_is_linked_to_a_valid_offerer(self, app):
            # Given
            beneficiary = create_user(email='beneficiary@example.com', first_name="Hermione", last_name="Granger")
            user = create_user()
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            stock = create_stock(offer=offer, price=0)
            date_created = datetime(2020, 4, 3, 12, 0, 0)
            booking = create_booking(user=beneficiary, stock=stock, token="ABCD", date_created=date_created, is_used=True)
            repository.save(user_offerer, booking)

            # When
            response = TestClient(app.test_client()) \
                .with_auth(user.email) \
                .get('/bookings/pro')

            # Then
            expected_bookings_recap = [
                {
                    'stock': {
                        'type': 'thing',
                        'offer_name': 'Test Book'
                    },
                    'beneficiary': {
                        'email': 'beneficiary@example.com',
                        'firstname': 'Hermione',
                        'lastname': 'Granger',
                    },
                    'booking_date': '2020-04-03T12:00:00Z',
                    'booking_token': 'ABCD',
                    'booking_status': 'validated',
                    'booking_is_duo': False
                }
            ]
            assert response.status_code == 200
            assert response.json == expected_bookings_recap

    class Returns401Test:
        @clean_database
        def when_user_is_admin(self, app):
            # Given
            user = create_user(is_admin=True, can_book_free_offers=False)
            repository.save(user)

            # When
            response = TestClient(app.test_client()) \
                .with_auth(user.email) \
                .get('/bookings/pro')

            # Then
            assert response.status_code == 401
            assert response.json == {
                'global': ["Le statut d'administrateur ne permet pas d'accéder au suivi des réservations"]
            }
