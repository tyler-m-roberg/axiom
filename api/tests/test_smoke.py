def test_app_imports() -> None:
    """Smoke test: the FastAPI app and its routers import without error."""
    from axiom_api.main import app

    assert app.title == "Axiom API"
    paths = {route.path for route in app.routes}
    assert "/healthz" in paths
    assert "/api/auth/me" in paths
    assert "/api/tests" in paths


def test_audit_diff() -> None:
    from axiom_api.services.audit import diff

    out = diff({"a": 1, "b": 2}, {"a": 1, "b": 3, "c": 4})
    assert out == {"b": {"before": 2, "after": 3}, "c": {"before": None, "after": 4}}


def test_field_models_round_trip() -> None:
    from axiom_api.models.metadata_field import (
        BindingApplies,
        BindingRequirement,
        FieldDataType,
        FieldScope,
        FieldStatus,
    )

    assert FieldDataType("string") is FieldDataType.STRING
    assert FieldScope("event") is FieldScope.EVENT
    assert FieldStatus("on_the_fly") is FieldStatus.ON_THE_FLY
    assert BindingRequirement("required") is BindingRequirement.REQUIRED
    assert BindingApplies("event") is BindingApplies.EVENT
