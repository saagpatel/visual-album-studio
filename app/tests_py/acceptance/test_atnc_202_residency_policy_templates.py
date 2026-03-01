from vas_studio import ResidencyTemplateServiceV1


def test_atnc_202_residency_policy_templates(runtime):
    service = ResidencyTemplateServiceV1(runtime.db)
    templates = service.list_templates()

    assert templates["ok"] is True
    assert len(templates["templates"]) >= 3

    applied = service.apply_template(project_id="proj_atnc202", template_id="tpl_global_balanced")
    assert applied["ok"] is True
    assert "eu-west-1" in applied["constraint"]["allowed_regions"]
