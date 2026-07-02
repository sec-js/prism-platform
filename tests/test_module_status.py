"""Tests for the standard module status enum and graceful degradation when a
key-dependent module has no API key (issue #61)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.module_status import (
    annotate,
    classify,
    reason_for,
    status_notice,
    OK,
    SKIPPED,
    RATE_LIMITED,
    ERROR,
    ALL,
)


class TestStatusNotice:
    def test_notice_for_skipped(self):
        result = annotate({}, SKIPPED, "No API key configured (SHODAN_API_KEY)")
        assert status_notice(result) == "Skipped: No API key configured (SHODAN_API_KEY)"

    def test_notice_for_rate_limited(self):
        result = annotate({}, RATE_LIMITED, "Shodan API rate limit reached")
        assert status_notice(result) == "Rate limited: Shodan API rate limit reached"

    def test_no_notice_for_ok_or_error(self):
        assert status_notice({"status": OK}) is None
        assert status_notice({"error": "boom"}) is None


class TestClassify:
    def test_explicit_status_is_honoured(self):
        assert classify({"status": SKIPPED}) == SKIPPED
        assert classify({"status": RATE_LIMITED, "error": "anything"}) == RATE_LIMITED

    def test_no_error_is_ok(self):
        assert classify({"error": None}) == OK
        assert classify({}) == OK

    def test_non_dict_is_ok(self):
        # Some modules (e.g. blackbird) return lists.
        assert classify([1, 2, 3]) == OK
        assert classify(None) == OK

    def test_missing_key_text_is_skipped(self):
        assert classify({"error": "SHODAN_API_KEY not set in .env"}) == SKIPPED
        assert classify({"error": "Leak-Lookup API key not configured"}) == SKIPPED
        assert classify({"error": "Invalid Censys credentials"}) == SKIPPED

    def test_rate_limit_text_is_rate_limited(self):
        assert classify({"error": "API returned 429: too many requests"}) == RATE_LIMITED
        assert classify({"error": "You have exceeded your quota"}) == RATE_LIMITED

    def test_generic_error_is_error(self):
        assert classify({"error": "Connection refused"}) == ERROR

    def test_invalid_explicit_status_falls_back(self):
        assert classify({"status": "bogus", "error": "boom"}) == ERROR


class TestAnnotate:
    def test_non_error_status_clears_error(self):
        result = {"error": "SHODAN_API_KEY not set"}
        annotate(result, SKIPPED, "No API key configured (SHODAN_API_KEY)")
        assert result["status"] == SKIPPED
        assert result["error"] is None
        assert result["status_reason"] == "No API key configured (SHODAN_API_KEY)"

    def test_error_status_keeps_error_semantics(self):
        result = {}
        annotate(result, ERROR, "Connection refused")
        assert result["status"] == ERROR
        assert result["status_reason"] == "Connection refused"

    def test_reason_for_prefers_status_reason(self):
        assert reason_for({"status_reason": "nice", "error": "raw"}) == "nice"
        assert reason_for({"error": "raw"}) == "raw"
        assert reason_for({}) is None

    def test_all_statuses_are_unique(self):
        assert ALL == (OK, SKIPPED, RATE_LIMITED, ERROR)
        assert len(set(ALL)) == 4


class TestKeyDependentModulesSkip:
    """Each key-dependent module should report `skipped` (not a hard error)
    when its API key is absent."""

    def test_shodan_skipped_without_key(self):
        from modules.shodan_lookup import ShodanLookup
        sh = ShodanLookup()
        sh.api_key = ""
        result = sh.host_info("8.8.8.8")
        assert classify(result) == SKIPPED
        assert result["error"] is None

    def test_virustotal_skipped_without_key(self):
        from modules.threat_intel import VirusTotal
        vt = VirusTotal()
        vt.api_key = ""
        result = vt.check_ip("8.8.8.8")
        assert classify(result) == SKIPPED

    def test_abuseipdb_skipped_without_key(self):
        from modules.threat_intel import AbuseIPDB
        adb = AbuseIPDB()
        adb.api_key = ""
        result = adb.check_ip("8.8.8.8")
        assert classify(result) == SKIPPED
        assert result["error"] is None

    def test_censys_skipped_without_key(self):
        from modules.censys_lookup import CensysLookup
        cl = CensysLookup()
        cl.api_id = ""
        cl.api_secret = ""
        assert classify(cl.search_ip("8.8.8.8")) == SKIPPED
        assert classify(cl.search_domain("example.com")) == SKIPPED

    def test_leak_lookup_skipped_without_key(self):
        from modules.leak_lookup import LeakLookup
        ll = LeakLookup()
        ll.leak_lookup_key = ""
        result = ll.check_leak_lookup("a@b.com")
        assert classify(result) == SKIPPED

    def test_telegram_id_skipped_without_token(self):
        from modules.telegram_lookup import TelegramLookup
        result = TelegramLookup().lookup_id("123456", bot_token=None)
        assert classify(result) == SKIPPED
        assert result["error"] is None


class TestReasonFor:
    def test_not_dict_

