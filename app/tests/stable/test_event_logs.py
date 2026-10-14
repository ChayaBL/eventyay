import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse

from eventyay.base.models import LogEntry
from eventyay.base.models.auth import StaffSession


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_event_logs_search_filters_results(organizer_client, organizer, event, user):
    content_type = ContentType.objects.get_for_model(event)

    matching_log = LogEntry.objects.create(
        event=event,
        content_type=content_type,
        object_id=event.pk,
        user=user,
        action_type="test.search.match",
        data='{"message": "unique needle"}',
    )
    LogEntry.objects.create(
        event=event,
        content_type=content_type,
        object_id=event.pk,
        user=user,
        action_type="test.search.other",
        data='{"message": "different entry"}',
    )

    url = reverse(
        "control:event.log",
        kwargs={"organizer": organizer.slug, "event": event.slug},
    )
    response = organizer_client.get(url, {"q": "test.search.match"})

    assert response.status_code == 200
    assert list(response.context["logs"]) == [matching_log]



@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_event_logs_search_data_requires_active_staff_session(
    organizer_client, staff_client, staff_user, organizer, event, user
):
    content_type = ContentType.objects.get_for_model(event)
    matching_log = LogEntry.objects.create(
        event=event,
        content_type=content_type,
        object_id=event.pk,
        user=user,
        action_type="test.search.payload",
        data='{"message": "private needle"}',
    )

    url = reverse(
        "control:event.log",
        kwargs={"organizer": organizer.slug, "event": event.slug},
    )

    organizer_response = organizer_client.get(url, {"q": "private needle"})
    assert organizer_response.status_code == 200
    assert matching_log not in organizer_response.context["logs"]

    session = staff_client.session
    session.save()
    StaffSession.objects.create(
        user=staff_user,
        session_key=session.session_key,
        comment="event log search test",
    )

    staff_response = staff_client.get(url, {"q": "private needle"})
    assert staff_response.status_code == 200
    assert matching_log in staff_response.context["logs"]
