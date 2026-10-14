import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from eventyay.base.models import LogEntry


@pytest.mark.django_db
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

    # Raw log data must not be searchable without an active staff session.
    response = organizer_client.get(url, {"q": "needle"})
    assert response.status_code == 200
    assert list(response.context["logs"]) == []

    # Visible action types remain searchable.
    response = organizer_client.get(url, {"q": "test.search.match"})
    assert response.status_code == 200
    assert list(response.context["logs"]) == [matching_log]
