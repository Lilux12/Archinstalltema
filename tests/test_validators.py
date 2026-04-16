"""Тесты валидаторов пользовательского ввода."""

import pytest

from arch_installer.utils.validators import (
    validate_hostname,
    validate_password,
    validate_username,
)


class TestValidateUsername:
    """Тесты валидации имени пользователя."""

    def test_valid_username(self) -> None:
        ok, msg = validate_username("ivan")
        assert ok is True
        assert msg == ""

    def test_valid_username_with_underscore(self) -> None:
        ok, _ = validate_username("_user")
        assert ok is True

    def test_valid_username_with_numbers(self) -> None:
        ok, _ = validate_username("user123")
        assert ok is True

    def test_valid_username_with_dash(self) -> None:
        ok, _ = validate_username("my-user")
        assert ok is True

    def test_empty_username(self) -> None:
        ok, msg = validate_username("")
        assert ok is False
        assert msg != ""

    def test_forbidden_root(self) -> None:
        ok, msg = validate_username("root")
        assert ok is False

    def test_forbidden_daemon(self) -> None:
        ok, msg = validate_username("daemon")
        assert ok is False

    def test_forbidden_bin(self) -> None:
        ok, msg = validate_username("bin")
        assert ok is False

    def test_forbidden_sys(self) -> None:
        ok, msg = validate_username("sys")
        assert ok is False

    def test_forbidden_nobody(self) -> None:
        ok, msg = validate_username("nobody")
        assert ok is False

    def test_starts_with_number(self) -> None:
        ok, msg = validate_username("1user")
        assert ok is False

    def test_uppercase(self) -> None:
        ok, msg = validate_username("User")
        assert ok is False

    def test_too_long(self) -> None:
        ok, msg = validate_username("a" * 33)
        assert ok is False

    def test_special_chars(self) -> None:
        ok, msg = validate_username("user@name")
        assert ok is False

    def test_spaces(self) -> None:
        ok, msg = validate_username("user name")
        assert ok is False


class TestValidatePassword:
    """Тесты валидации пароля."""

    def test_valid_password(self) -> None:
        ok, msg = validate_password("securepass123")
        assert ok is True
        assert msg == ""

    def test_min_length(self) -> None:
        ok, _ = validate_password("123456")
        assert ok is True

    def test_too_short(self) -> None:
        ok, msg = validate_password("12345")
        assert ok is False

    def test_empty(self) -> None:
        ok, msg = validate_password("")
        assert ok is False

    def test_long_password(self) -> None:
        ok, _ = validate_password("a" * 100)
        assert ok is True


class TestValidateHostname:
    """Тесты валидации hostname (RFC 1123)."""

    def test_valid_hostname(self) -> None:
        ok, msg = validate_hostname("archlinux")
        assert ok is True
        assert msg == ""

    def test_valid_with_numbers(self) -> None:
        ok, _ = validate_hostname("server01")
        assert ok is True

    def test_valid_with_dashes(self) -> None:
        ok, _ = validate_hostname("my-server")
        assert ok is True

    def test_empty(self) -> None:
        ok, msg = validate_hostname("")
        assert ok is False

    def test_too_long(self) -> None:
        ok, msg = validate_hostname("a" * 64)
        assert ok is False

    def test_starts_with_dash(self) -> None:
        ok, msg = validate_hostname("-server")
        assert ok is False

    def test_ends_with_dash(self) -> None:
        ok, msg = validate_hostname("server-")
        assert ok is False

    def test_special_chars(self) -> None:
        ok, msg = validate_hostname("server_name")
        assert ok is False

    def test_spaces(self) -> None:
        ok, msg = validate_hostname("my server")
        assert ok is False

    def test_dots_allowed_fqdn(self) -> None:
        """RFC 1123 допускает точки в полных доменных именах."""
        ok, _ = validate_hostname("my.server")
        assert ok is True
