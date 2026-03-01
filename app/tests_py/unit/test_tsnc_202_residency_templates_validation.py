from vas_studio import ResidencyTemplateServiceV1


def test_tsnc_202_template_validation_success(runtime):
    service = ResidencyTemplateServiceV1(runtime.db)
    valid = service.validate_template(
        {
            "home_region": "us-west-1",
            "active_regions": ["us-west-1", "us-east-1"],
            "dr_region": "eu-west-1",
            "allowed_regions": ["us-west-1", "us-east-1", "eu-west-1"],
        }
    )
    assert valid["ok"] is True


def test_tsnc_202_template_validation_fails_when_home_not_active(runtime):
    service = ResidencyTemplateServiceV1(runtime.db)
    invalid = service.validate_template(
        {
            "home_region": "us-west-1",
            "active_regions": ["us-east-1"],
            "dr_region": "eu-west-1",
            "allowed_regions": ["us-east-1", "eu-west-1"],
        }
    )
    assert invalid["ok"] is False
    assert invalid["error_code"] == "E_TEMPLATE_HOME_NOT_ACTIVE"
