"""Tests for XML payload builders."""

from unittest import TestCase
import logging
import xml.etree.ElementTree as ET

from yahoofantasy.api.xml_builder import (
    build_roster_change_xml,
    build_add_player_xml,
    build_drop_player_xml,
    build_add_drop_xml,
    build_waiver_claim_xml,
    build_cancel_waiver_xml,
)


class TestXMLBuilder(TestCase):
    def _parse_xml(self, xml_str):
        """Helper to parse XML string, stripping declaration."""
        # Remove XML declaration for easier parsing
        if xml_str.startswith("<?xml"):
            xml_str = xml_str.split("?>", 1)[1]
        return ET.fromstring(xml_str)

    def test_build_roster_change_xml_basic(self):
        logging.info("xml_builder.build_roster_change_xml creates valid XML structure")
        xml = build_roster_change_xml(
            coverage_type="week",
            week=16,
            players=[{"player_key": "nba.p.5007", "position": "PG"}],
        )

        root = self._parse_xml(xml)
        self.assertEqual(root.tag, "fantasy_content")

        roster = root.find("roster")
        self.assertIsNotNone(roster)

        cov_type = roster.find("coverage_type")
        self.assertEqual(cov_type.text, "week")

        week = roster.find("week")
        self.assertEqual(week.text, "16")

        players = roster.find("players")
        player = players.find("player")
        self.assertEqual(player.find("player_key").text, "nba.p.5007")
        self.assertEqual(player.find("position").text, "PG")

    def test_build_roster_change_xml_multiple_players(self):
        logging.info("xml_builder.build_roster_change_xml handles multiple players")
        xml = build_roster_change_xml(
            coverage_type="week",
            week=16,
            players=[
                {"player_key": "nba.p.5007", "position": "PG"},
                {"player_key": "nba.p.4892", "position": "BN"},
            ],
        )

        root = self._parse_xml(xml)
        players = root.find("roster").find("players")
        player_elems = players.findall("player")
        self.assertEqual(len(player_elems), 2)
        self.assertEqual(player_elems[0].find("player_key").text, "nba.p.5007")
        self.assertEqual(player_elems[1].find("player_key").text, "nba.p.4892")

    def test_build_add_player_xml(self):
        logging.info("xml_builder.build_add_player_xml creates valid add transaction XML")
        xml = build_add_player_xml("nba.p.5007", "418.l.12345.t.1")

        root = self._parse_xml(xml)
        self.assertEqual(root.tag, "fantasy_content")

        transaction = root.find("transaction")
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.find("type").text, "add")

        player = transaction.find("players").find("player")
        self.assertEqual(player.find("player_key").text, "nba.p.5007")

        tx_data = player.find("transaction_data")
        self.assertEqual(tx_data.find("type").text, "add")
        self.assertEqual(tx_data.find("destination_team_key").text, "418.l.12345.t.1")

    def test_build_drop_player_xml(self):
        logging.info("xml_builder.build_drop_player_xml creates valid drop transaction XML")
        xml = build_drop_player_xml("nba.p.5007", "418.l.12345.t.1")

        root = self._parse_xml(xml)
        transaction = root.find("transaction")
        self.assertEqual(transaction.find("type").text, "drop")

        player = transaction.find("players").find("player")
        self.assertEqual(player.find("player_key").text, "nba.p.5007")

        tx_data = player.find("transaction_data")
        self.assertEqual(tx_data.find("type").text, "drop")
        self.assertEqual(tx_data.find("source_team_key").text, "418.l.12345.t.1")

    def test_build_add_drop_xml(self):
        logging.info("xml_builder.build_add_drop_xml creates valid add/drop transaction XML")
        xml = build_add_drop_xml(
            add_player_key="nba.p.5007",
            destination_team_key="418.l.12345.t.1",
            drop_player_key="nba.p.4892",
            source_team_key="418.l.12345.t.1",
        )

        root = self._parse_xml(xml)
        transaction = root.find("transaction")
        self.assertEqual(transaction.find("type").text, "add/drop")

        players = transaction.find("players").findall("player")
        self.assertEqual(len(players), 2)

        # First player is add
        add_player = players[0]
        self.assertEqual(add_player.find("player_key").text, "nba.p.5007")
        self.assertEqual(add_player.find("transaction_data").find("type").text, "add")

        # Second player is drop
        drop_player = players[1]
        self.assertEqual(drop_player.find("player_key").text, "nba.p.4892")
        self.assertEqual(drop_player.find("transaction_data").find("type").text, "drop")

    def test_build_waiver_claim_xml_simple(self):
        logging.info("xml_builder.build_waiver_claim_xml creates valid waiver claim XML")
        xml = build_waiver_claim_xml("nba.p.5007", "418.l.12345.t.1")

        root = self._parse_xml(xml)
        transaction = root.find("transaction")
        self.assertEqual(transaction.find("type").text, "add")

        # No FAAB bid
        self.assertIsNone(transaction.find("faab_bid"))

        player = transaction.find("players").find("player")
        self.assertEqual(player.find("player_key").text, "nba.p.5007")

    def test_build_waiver_claim_xml_with_faab(self):
        logging.info("xml_builder.build_waiver_claim_xml includes FAAB bid when provided")
        xml = build_waiver_claim_xml("nba.p.5007", "418.l.12345.t.1", faab_bid=15)

        root = self._parse_xml(xml)
        transaction = root.find("transaction")

        faab_bid = transaction.find("faab_bid")
        self.assertIsNotNone(faab_bid)
        self.assertEqual(faab_bid.text, "15")

    def test_build_waiver_claim_xml_with_drop(self):
        logging.info("xml_builder.build_waiver_claim_xml handles add/drop waiver claim")
        xml = build_waiver_claim_xml(
            "nba.p.5007",
            "418.l.12345.t.1",
            faab_bid=20,
            drop_player_key="nba.p.4892",
            source_team_key="418.l.12345.t.1",
        )

        root = self._parse_xml(xml)
        transaction = root.find("transaction")

        # Type should be add/drop when dropping
        self.assertEqual(transaction.find("type").text, "add/drop")

        players = transaction.find("players").findall("player")
        self.assertEqual(len(players), 2)

    def test_build_cancel_waiver_xml(self):
        logging.info("xml_builder.build_cancel_waiver_xml creates valid cancel XML")
        xml = build_cancel_waiver_xml("418.l.12345.tr.123")

        root = self._parse_xml(xml)
        transaction = root.find("transaction")

        self.assertEqual(transaction.find("transaction_key").text, "418.l.12345.tr.123")
        self.assertEqual(transaction.find("action").text, "cancel")

    def test_xml_declaration_present(self):
        logging.info("xml_builder functions include XML declaration")
        xml = build_add_player_xml("nba.p.5007", "418.l.12345.t.1")
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
