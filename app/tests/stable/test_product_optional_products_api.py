
import pytest
from django_scopes import scope, scopes_disabled
from rest_framework.test import APIClient

from eventyay.base.models import Product, ProductVariation


@pytest.fixture
def token_client(team):
    client = APIClient()
    token = team.tokens.create(name='Optional products API tests')
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.token)
    return client


def question_url(organizer, event):
    return f'/api/v1/organizers/{organizer.slug}/events/{event.slug}/questions/'


def quota_url(organizer, event):
    return f'/api/v1/organizers/{organizer.slug}/events/{event.slug}/quotas/'


@pytest.mark.django_db
def test_create_question_without_products(token_client, organizer, event):
    response = token_client.post(
        question_url(organizer, event),
        {
            'question': 'Your name?',
            'type': 'S',
            'required': False,
            'identifier': None,
        },
        format='json',
    )

    assert response.status_code == 201

    with scopes_disabled():
        question = event.questions.get(pk=response.data['id'])
        assert not question.products.exists()


@pytest.mark.django_db
def test_create_quota_without_products(token_client, organizer, event):
    response = token_client.post(
        quota_url(organizer, event),
        {
            'name': 'Main quota',
            'size': 10,
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['products'] == []
    assert response.data['variations'] == []


@pytest.mark.django_db
def test_create_quota_with_variations_but_without_products(
    token_client, organizer, event
):
    with scope(organizer=organizer, event=event):
        product = Product.objects.create(
            event=event,
            name='Ticket',
            default_price=10,
        )
        variation = ProductVariation.objects.create(
            product=product,
            value='Adult',
        )

    response = token_client.post(
        quota_url(organizer, event),
        {
            'name': 'Main quota',
            'size': 10,
            'variations': [variation.pk],
        },
        format='json',
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_quota_with_product_variations_but_without_variations(
    token_client, organizer, event
):
    with scope(organizer=organizer, event=event):
        product = Product.objects.create(
            event=event,
            name='Ticket',
            default_price=10,
        )
        ProductVariation.objects.create(
            product=product,
            value='Adult',
        )

    response = token_client.post(
        quota_url(organizer, event),
        {
            'name': 'Main quota',
            'size': 10,
            'products': [product.pk],
        },
        format='json',
    )

    assert response.status_code == 400
