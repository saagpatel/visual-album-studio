from vas_studio import CollaborationTimelineServiceV1


def test_tsnc_103_timeline_sort_key_order(runtime):
    service = CollaborationTimelineServiceV1(runtime.db)
    events = [
        {"event_id": "b", "sequence": 2, "created_at": 10},
        {"event_id": "a", "sequence": 1, "created_at": 20},
        {"event_id": "c", "sequence": 2, "created_at": 5},
    ]
    events.sort(key=service._sort_key)

    assert [item["event_id"] for item in events] == ["a", "c", "b"]
