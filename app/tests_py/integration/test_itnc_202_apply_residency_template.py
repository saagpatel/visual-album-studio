from vas_studio import ResidencyTemplateServiceV1


def test_itnc_202_apply_template_updates_policy(runtime):
    service = ResidencyTemplateServiceV1(runtime.db)

    applied = service.apply_template(project_id="proj_itnc202", template_id="tpl_us_default")
    assert applied["ok"] is True
    assert applied["constraint"]["home_region"] == "us-west-1"

    missing = service.apply_template(project_id="proj_itnc202", template_id="missing_template")
    assert missing["ok"] is False
    assert missing["error_code"] == "E_TEMPLATE_NOT_FOUND"
