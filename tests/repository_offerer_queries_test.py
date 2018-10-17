import secrets

import pytest

from models import PcObject
from repository.offerer_queries import find_all_admin_offerer_emails, find_all_offerers_siren_with_user_informations, \
     find_all_offerers_siren_with_user_informations_and_venue, find_all_offerers_siren_with_user_informations_and_not_virtual_venue, find_all_offerers_with_venue
from tests.conftest import clean_database
from utils.test_utils import create_user, create_offerer, create_user_offerer, create_venue


@pytest.mark.standalone
@clean_database
def test_find_all_admin_offerer_emails(app):
    # Given
    offerer = create_offerer()
    user_admin1 = create_user(email='admin1@offerer.com')
    user_admin2 = create_user(email='admin2@offerer.com')
    user_editor = create_user(email='editor@offerer.com')
    user_admin_not_validated = create_user(email='admin_not_validated@offerer.com')
    user_random = create_user(email='random@user.com')
    user_offerer_admin1 = create_user_offerer(user_admin1, offerer, is_admin=True)
    user_offerer_admin2 = create_user_offerer(user_admin2, offerer, is_admin=True)
    user_offerer_admin_not_validated = create_user_offerer(user_admin_not_validated, offerer,
                                                           validation_token=secrets.token_urlsafe(20), is_admin=True)
    user_offerer_editor = create_user_offerer(user_editor, offerer, is_admin=False)
    PcObject.check_and_save(user_random, user_offerer_admin1, user_offerer_admin2, user_offerer_admin_not_validated,
                            user_offerer_editor)

    # When
    emails = find_all_admin_offerer_emails(offerer.id)

    # Then
    assert set(emails) == {'admin1@offerer.com', 'admin2@offerer.com'}
    assert type(emails) == list

@pytest.mark.standalone
@clean_database
def test_find_all_offerers_siren_with_user_informations(app):
    #given
    user_admin1 = create_user(email='admin1@offerer.com')
    user_admin2 = create_user(email='admin2@offerer.com')
    user_editor1 =  create_user(email='editor1@offerer.com')
    offerer1 = create_offerer(name='offerer1')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    user_offerer1 = create_user_offerer(user_admin1, offerer1, is_admin=True)
    user_offerer2 = create_user_offerer(user_editor1, offerer1, is_admin=False)
    user_offerer3 = create_user_offerer(user_admin1, offerer2, is_admin=True)
    user_offerer4 = create_user_offerer(user_admin2, offerer2, is_admin=True)
    PcObject.check_and_save(user_admin1, user_admin2, user_editor1, offerer1, offerer2, user_offerer1, user_offerer2, user_offerer3, user_offerer4)

    #when
    offerers = find_all_offerers_siren_with_user_informations()

    #then
    assert len(offerers) == 4
    assert (offerer1.name, offerer1.siren, offerer1.postalCode, offerer1.city, user_admin1.firstName, user_admin1.lastName, user_admin1.email, user_admin1.phoneNumber, user_admin1.postalCode) in offerers
    assert (offerer1.name, offerer1.siren, offerer1.postalCode, offerer1.city, user_editor1.firstName, user_editor1.lastName, user_editor1.email, user_editor1.phoneNumber, user_editor1.postalCode) in offerers
    assert (offerer2.name, offerer2.siren, offerer2.postalCode, offerer2.city, user_admin1.firstName, user_admin1.lastName, user_admin1.email, user_admin1.phoneNumber, user_admin1.postalCode) in offerers
    assert (offerer2.name, offerer2.siren, offerer2.postalCode, offerer2.city, user_admin2.firstName, user_admin2.lastName, user_admin2.email, user_admin2.phoneNumber, user_admin2.postalCode) in offerers

@pytest.mark.standalone
@clean_database
def test_find_all_offerers_siren_with_user_informations_and_venue(app):
    #given
    user_admin1 = create_user(email='admin1@offerer.com')
    user_admin2 = create_user(email='admin2@offerer.com')
    user_editor1 =  create_user(email='editor1@offerer.com')
    offerer1 = create_offerer(name='offerer1')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    venue1 = create_venue(offerer1)
    venue2 = create_venue(offerer2)
    venue3 = create_venue(offerer2)
    user_offerer1 = create_user_offerer(user_admin1, offerer1, is_admin=True)
    user_offerer2 = create_user_offerer(user_editor1, offerer1, is_admin=False)
    user_offerer3 = create_user_offerer(user_admin1, offerer2, is_admin=True)
    user_offerer4 = create_user_offerer(user_admin2, offerer2, is_admin=True)
    PcObject.check_and_save(user_admin1, user_admin2, user_editor1, offerer1, offerer2, venue1, venue2, venue3,  user_offerer1, user_offerer2, user_offerer3, user_offerer4)

    #when
    offerers = find_all_offerers_siren_with_user_informations_and_venue()

    #then
    assert len(offerers) == 6
    assert (offerer1.name, offerer1.siren, offerer1.postalCode, offerer1.city, venue1.name, venue1.bookingEmail, venue1.postalCode, user_admin1.firstName, user_admin1.lastName, user_admin1.email, user_admin1.phoneNumber, user_admin1.postalCode) in offerers
    assert (offerer1.name, offerer1.siren, offerer1.postalCode, offerer1.city, venue1.name, venue1.bookingEmail, venue1.postalCode, user_editor1.firstName, user_editor1.lastName, user_editor1.email, user_editor1.phoneNumber, user_editor1.postalCode) in offerers
    assert (offerer2.name, offerer2.siren, offerer2.postalCode, offerer2.city, venue2.name, venue2.bookingEmail, venue2.postalCode, user_admin1.firstName, user_admin1.lastName, user_admin1.email, user_admin1.phoneNumber, user_admin1.postalCode) in offerers
    assert (offerer2.name, offerer2.siren, offerer2.postalCode, offerer2.city, venue2.name, venue2.bookingEmail, venue2.postalCode, user_admin2.firstName, user_admin2.lastName, user_admin2.email, user_admin2.phoneNumber, user_admin2.postalCode) in offerers
    assert (offerer2.name, offerer2.siren, offerer2.postalCode, offerer2.city, venue3.name, venue3.bookingEmail, venue3.postalCode, user_admin1.firstName, user_admin1.lastName, user_admin1.email, user_admin1.phoneNumber, user_admin1.postalCode) in offerers
    assert (offerer2.name, offerer2.siren, offerer2.postalCode, offerer2.city, venue3.name, venue3.bookingEmail, venue3.postalCode, user_admin2.firstName, user_admin2.lastName, user_admin2.email, user_admin2.phoneNumber, user_admin2.postalCode) in offerers


@pytest.mark.standalone
@clean_database
def test_find_all_offerers_siren_with_user_informations_and_not_virtual_venue(app):
    #given
    user_admin1 = create_user(email='admin1@offerer.com')
    user_admin2 = create_user(email='admin2@offerer.com')
    user_editor1 =  create_user(email='editor1@offerer.com')
    offerer1 = create_offerer(name='offerer1')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    venue1 = create_venue(offerer1, is_virtual=True)
    venue2 = create_venue(offerer2, is_virtual=True)
    venue3 = create_venue(offerer2, is_virtual=False)
    user_offerer1 = create_user_offerer(user_admin1, offerer1, is_admin=True)
    user_offerer2 = create_user_offerer(user_editor1, offerer1, is_admin=False)
    user_offerer3 = create_user_offerer(user_admin1, offerer2, is_admin=True)
    user_offerer4 = create_user_offerer(user_admin2, offerer2, is_admin=True)
    PcObject.check_and_save(user_admin1, user_admin2, user_editor1, offerer1, offerer2, venue1, venue2, venue3,  user_offerer1, user_offerer2, user_offerer3, user_offerer4)

    #when
    offerers = find_all_offerers_siren_with_user_informations_and_not_virtual_venue()

    #then
    assert len(offerers) == 2
    assert (offerer2.name, offerer2.siren, offerer2.postalCode, offerer2.city, venue3.name, venue3.bookingEmail, venue3.postalCode, user_admin1.firstName, user_admin1.lastName, user_admin1.email, user_admin1.phoneNumber, user_admin1.postalCode) in offerers
    assert (offerer2.name, offerer2.siren, offerer2.postalCode, offerer2.city, venue3.name, venue3.bookingEmail, venue3.postalCode, user_admin2.firstName, user_admin2.lastName, user_admin2.email, user_admin2.phoneNumber, user_admin2.postalCode) in offerers


@pytest.mark.standalone
@clean_database
def test_find_all_offerers_with_venue(app):
    #given
    offerer1 = create_offerer(name='offerer1')
    offerer2 = create_offerer(name='offerer2', siren='789456123')
    venue1 = create_venue(offerer1, is_virtual=True)
    venue2 = create_venue(offerer2, is_virtual=True)
    venue3 = create_venue(offerer2, is_virtual=False)
    PcObject.check_and_save(offerer1, offerer2, venue1, venue2, venue3)

    #when
    offerers = find_all_offerers_with_venue()

    #then
    assert len(offerers) == 3
    assert(offerer1.id, offerer1.name, venue1.id, venue1.name, venue1.bookingEmail, venue1.postalCode, venue1.isVirtual) in offerers
    assert(offerer2.id, offerer2.name, venue2.id, venue2.name, venue2.bookingEmail, venue2.postalCode, venue2.isVirtual) in offerers
    assert(offerer2.id, offerer2.name, venue3.id, venue3.name, venue3.bookingEmail, venue3.postalCode, venue3.isVirtual) in offerers

