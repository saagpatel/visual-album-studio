import pytest

from vas_studio import JobState, VasError


def test_ts004_job_state_transitions():
    job = JobState(job_id="job_1")
    job.transition("running")
    job.transition("paused")
    job.transition("running")
    job.transition("succeeded")
    assert job.status == "succeeded"

    with pytest.raises(VasError):
        job.transition("queued")
