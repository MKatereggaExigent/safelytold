import pytest

from services.notification_service.app import templates


def test_render_neutral_template_in_known_locale() -> None:
    subject = templates.render_subject('mailbox_nudge_v1', 'en')
    body = templates.render_body('mailbox_nudge_v1', 'en')
    assert subject
    assert body
    assert subject != body


def test_all_locales_have_all_templates() -> None:
    for locale in templates.list_locales():
        for code in templates.list_templates():
            assert templates.render_subject(code, locale)
            assert templates.render_body(code, locale)


def test_unknown_template_code_raises() -> None:
    with pytest.raises(KeyError):
        templates.render_subject('not_a_template', 'en')


def test_unknown_locale_raises() -> None:
    with pytest.raises(ValueError):
        templates.render_body('mailbox_nudge_v1', 'xx')
