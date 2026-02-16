from vas_studio import UxPlatformService


def test_it009_export_command_center_recoverability(runtime):
    ux = UxPlatformService(runtime.db)
    center = ux.build_export_command_center(
        [
            {"id": "job1", "status": "queued"},
            {"id": "job2", "status": "running"},
            {"id": "job3", "status": "failed"},
            {"id": "job4", "status": "failed"},
        ]
    )

    assert len(center["buckets"]["failed"]) == 2
    assert len(center["recovery_actions"]) == 2
    for action in center["recovery_actions"]:
        assert "resume" in action["actions"]
        assert "cleanup" in action["actions"]
