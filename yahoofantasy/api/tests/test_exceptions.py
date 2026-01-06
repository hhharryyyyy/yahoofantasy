"""Tests for custom exception classes."""

from unittest import TestCase
import logging

from yahoofantasy.exceptions import (
    YahooFantasyError,
    RosterError,
    TransactionError,
    InvalidPositionError,
    RosterFullError,
    PlayerNotAvailableError,
    InsufficientFAABError,
    WaiverPriorityError,
    InsufficientScopeError,
)


class TestExceptions(TestCase):
    def test_base_exception_attributes(self):
        logging.info("exceptions.YahooFantasyError stores code and raw_response")
        exc = YahooFantasyError("Test error", code=400, raw_response="<xml/>")

        self.assertEqual(str(exc), "Test error")
        self.assertEqual(exc.code, 400)
        self.assertEqual(exc.raw_response, "<xml/>")

    def test_exception_hierarchy(self):
        logging.info("exceptions module has correct inheritance hierarchy")
        # RosterError and TransactionError inherit from YahooFantasyError
        self.assertTrue(issubclass(RosterError, YahooFantasyError))
        self.assertTrue(issubclass(TransactionError, YahooFantasyError))

        # Specific roster errors inherit from RosterError
        self.assertTrue(issubclass(InvalidPositionError, RosterError))

        # Specific transaction errors inherit from TransactionError
        self.assertTrue(issubclass(RosterFullError, TransactionError))
        self.assertTrue(issubclass(PlayerNotAvailableError, TransactionError))
        self.assertTrue(issubclass(InsufficientFAABError, TransactionError))
        self.assertTrue(issubclass(WaiverPriorityError, TransactionError))

        # InsufficientScopeError inherits from base
        self.assertTrue(issubclass(InsufficientScopeError, YahooFantasyError))

    def test_can_catch_with_base_class(self):
        logging.info("exceptions can be caught using base class")
        try:
            raise PlayerNotAvailableError("Player not available")
        except TransactionError as e:
            self.assertIn("not available", str(e))
        except Exception:
            self.fail("Should have been caught as TransactionError")

        try:
            raise InvalidPositionError("Invalid position")
        except RosterError as e:
            self.assertIn("position", str(e))
        except Exception:
            self.fail("Should have been caught as RosterError")

    def test_exception_with_optional_params(self):
        logging.info("exceptions work with optional parameters")
        # Just message
        exc1 = YahooFantasyError("Simple error")
        self.assertEqual(str(exc1), "Simple error")
        self.assertIsNone(exc1.code)
        self.assertIsNone(exc1.raw_response)

        # With all params
        exc2 = PlayerNotAvailableError(
            "Player taken", code=400, raw_response="<error>Player taken</error>"
        )
        self.assertEqual(exc2.code, 400)
        self.assertIn("Player taken", exc2.raw_response)
