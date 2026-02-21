from unittest.mock import patch

import pytest
from fastapi import HTTPException

from service.micro_savings.app.exceptions.exceptions import (
    handle_exception,
    EXCEPTION_MAP,
)


class TestExceptionMapStructure:
    def test_all_entries_have_status_code(self):
        for exc_class, mapping in EXCEPTION_MAP.items():
            assert "status_code" in mapping, f"{exc_class} missing status_code"

    def test_all_entries_have_message(self):
        for exc_class, mapping in EXCEPTION_MAP.items():
            assert "message" in mapping, f"{exc_class} missing message"

    def test_all_status_codes_are_valid_http(self):
        valid_codes = {400, 422, 500, 501}
        for exc_class, mapping in EXCEPTION_MAP.items():
            assert mapping["status_code"] in valid_codes

    def test_exception_base_class_is_fallback(self):
        assert Exception in EXCEPTION_MAP


class TestHandleException:
    def test_value_error_returns_400(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(ValueError("bad input"))
        assert exc_info.value.status_code == 400

    def test_type_error_returns_400(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(TypeError("wrong type"))
        assert exc_info.value.status_code == 400

    def test_key_error_returns_400(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(KeyError("missing key"))
        assert exc_info.value.status_code == 400

    def test_zero_division_returns_400(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(ZeroDivisionError("division by zero"))
        assert exc_info.value.status_code == 400

    def test_overflow_error_returns_400(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(OverflowError("overflow"))
        assert exc_info.value.status_code == 400

    def test_arithmetic_error_returns_400(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(ArithmeticError("arithmetic"))
        assert exc_info.value.status_code == 400

    def test_not_implemented_returns_501(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(NotImplementedError("not implemented"))
        assert exc_info.value.status_code == 501

    def test_runtime_error_returns_500(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(RuntimeError("something crashed"))
        assert exc_info.value.status_code == 500

    def test_generic_exception_returns_500(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(Exception("unknown"))
        assert exc_info.value.status_code == 500


class TestHandleExceptionDetail:
    def test_live_message_appended_to_default(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(ValueError("amount cannot be negative"))
        assert "amount cannot be negative" in exc_info.value.detail
        assert EXCEPTION_MAP[ValueError]["message"] in exc_info.value.detail

    def test_empty_exception_message_uses_default_only(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(ValueError(""))
        assert exc_info.value.detail == EXCEPTION_MAP[ValueError]["message"]

    def test_detail_is_string(self):
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(RuntimeError("oops"))
        assert isinstance(exc_info.value.detail, str)


class TestHandleExceptionFallback:
    def test_unknown_exception_type_falls_back_to_exception_mapping(self):
        class CustomError(Exception):
            pass

        with pytest.raises(HTTPException) as exc_info:
            handle_exception(CustomError("custom error"))
        assert exc_info.value.status_code == EXCEPTION_MAP[Exception]["status_code"]

    def test_subclass_of_mapped_exception_resolves_correctly(self):
        # ZeroDivisionError is a subclass of ArithmeticError
        # but it has its own explicit entry — that should win
        with pytest.raises(HTTPException) as exc_info:
            handle_exception(ZeroDivisionError("div by zero"))
        assert (
                exc_info.value.status_code
                == EXCEPTION_MAP[ZeroDivisionError]["status_code"]
        )

    def test_subclass_without_own_entry_walks_mro(self):
        class CustomArithmetic(ArithmeticError):
            pass

        with pytest.raises(HTTPException) as exc_info:
            handle_exception(CustomArithmetic("custom arithmetic"))
        assert (
                exc_info.value.status_code == EXCEPTION_MAP[ArithmeticError]["status_code"]
        )


class TestHandleExceptionLogging:
    def test_error_is_logged(self):
        with patch("service.micro_savings.app.utils.exceptions.logger") as mock_logger:
            with pytest.raises(HTTPException):
                handle_exception(ValueError("log this"))
            mock_logger.error.assert_called_once()

    def test_log_contains_exception_class_name(self):
        with patch("service.micro_savings.app.utils.exceptions.logger") as mock_logger:
            with pytest.raises(HTTPException):
                handle_exception(ValueError("log this"))
            call_kwargs = mock_logger.error.call_args
            assert "ValueError" in str(call_kwargs)

    def test_log_contains_status_code(self):
        with patch("service.micro_savings.app.utils.exceptions.logger") as mock_logger:
            with pytest.raises(HTTPException):
                handle_exception(ValueError("log this"))
            call_kwargs = mock_logger.error.call_args
            assert "400" in str(call_kwargs)
