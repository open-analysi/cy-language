"""Tests for Network Address Utility Functions."""

from cy_language.native_functions import is_ip, is_ipv4, is_ipv6

# ============================================================================
# IPv4 Validation Tests
# ============================================================================


class TestIsIPv4:
    """Test cases for is_ipv4() function."""

    def test_valid_ipv4_standard(self):
        """Test valid standard IPv4 addresses."""
        assert is_ipv4("192.168.1.1") is True
        assert is_ipv4("10.0.0.1") is True
        assert is_ipv4("172.16.0.1") is True
        assert is_ipv4("8.8.8.8") is True

    def test_valid_ipv4_localhost(self):
        """Test localhost addresses."""
        assert is_ipv4("127.0.0.1") is True
        assert is_ipv4("127.0.0.0") is True
        assert is_ipv4("127.255.255.255") is True

    def test_valid_ipv4_boundaries(self):
        """Test boundary values."""
        assert is_ipv4("0.0.0.0") is True
        assert is_ipv4("255.255.255.255") is True
        assert is_ipv4("1.1.1.1") is True
        assert is_ipv4("254.254.254.254") is True

    def test_valid_ipv4_private_ranges(self):
        """Test private IP ranges."""
        # Class A private
        assert is_ipv4("10.0.0.0") is True
        assert is_ipv4("10.255.255.255") is True

        # Class B private
        assert is_ipv4("172.16.0.0") is True
        assert is_ipv4("172.31.255.255") is True

        # Class C private
        assert is_ipv4("192.168.0.0") is True
        assert is_ipv4("192.168.255.255") is True

    def test_invalid_ipv4_out_of_range(self):
        """Test octets out of range."""
        assert is_ipv4("256.1.1.1") is False
        assert is_ipv4("1.256.1.1") is False
        assert is_ipv4("1.1.256.1") is False
        assert is_ipv4("1.1.1.256") is False
        assert is_ipv4("300.300.300.300") is False

    def test_invalid_ipv4_incomplete(self):
        """Test incomplete addresses."""
        assert is_ipv4("192.168.1") is False
        assert is_ipv4("192.168") is False
        assert is_ipv4("192") is False

    def test_invalid_ipv4_too_many_octets(self):
        """Test addresses with too many octets."""
        assert is_ipv4("192.168.1.1.1") is False
        assert is_ipv4("1.2.3.4.5.6") is False

    def test_invalid_ipv4_non_numeric(self):
        """Test addresses with non-numeric characters."""
        assert is_ipv4("192.168.1.a") is False
        assert is_ipv4("a.b.c.d") is False
        assert is_ipv4("192.168.1.1x") is False

    def test_invalid_ipv4_empty_or_spaces(self):
        """Test empty or whitespace strings."""
        assert is_ipv4("") is False
        assert is_ipv4(" ") is False
        assert is_ipv4("   ") is False
        assert is_ipv4("192.168. 1.1") is False

    def test_invalid_ipv4_special_chars(self):
        """Test addresses with special characters."""
        assert is_ipv4("192-168-1-1") is False
        assert is_ipv4("192_168_1_1") is False
        assert is_ipv4("192/168/1/1") is False

    def test_invalid_ipv4_ipv6_addresses(self):
        """Test that IPv6 addresses are not valid IPv4."""
        assert is_ipv4("::1") is False
        assert is_ipv4("2001:db8::1") is False
        assert is_ipv4("fe80::1") is False

    def test_invalid_ipv4_wrong_type(self):
        """Test with non-string types."""
        assert is_ipv4(123) is False
        assert is_ipv4(None) is False
        assert is_ipv4([192, 168, 1, 1]) is False
        assert is_ipv4({"ip": "192.168.1.1"}) is False


# ============================================================================
# IPv6 Validation Tests
# ============================================================================


class TestIsIPv6:
    """Test cases for is_ipv6() function."""

    def test_valid_ipv6_standard(self):
        """Test valid standard IPv6 addresses."""
        assert is_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
        assert is_ipv6("2001:db8:85a3::8a2e:370:7334") is True
        assert is_ipv6("2001:db8::1") is True

    def test_valid_ipv6_localhost(self):
        """Test localhost address."""
        assert is_ipv6("::1") is True

    def test_valid_ipv6_unspecified(self):
        """Test unspecified address."""
        assert is_ipv6("::") is True

    def test_valid_ipv6_compressed(self):
        """Test compressed notation."""
        assert is_ipv6("fe80::1") is True
        assert is_ipv6("::ffff:192.0.2.1") is True  # IPv4-mapped
        assert is_ipv6("2001:db8::8a2e:370:7334") is True

    def test_valid_ipv6_link_local(self):
        """Test link-local addresses."""
        assert is_ipv6("fe80::") is True
        assert is_ipv6("fe80::1") is True
        assert is_ipv6("fe80::dead:beef") is True

    def test_valid_ipv6_multicast(self):
        """Test multicast addresses."""
        assert is_ipv6("ff00::") is True
        assert is_ipv6("ff02::1") is True
        assert is_ipv6("ff02::2") is True

    def test_valid_ipv6_documentation(self):
        """Test documentation addresses."""
        assert is_ipv6("2001:db8::") is True
        assert is_ipv6("2001:db8:1234:5678::1") is True

    def test_invalid_ipv6_too_many_groups(self):
        """Test addresses with too many groups."""
        assert is_ipv6("2001:db8:1:2:3:4:5:6:7") is False

    def test_invalid_ipv6_invalid_hex(self):
        """Test addresses with invalid hex characters."""
        assert is_ipv6("gggg::1") is False
        assert is_ipv6("2001:xyz::1") is False
        assert is_ipv6("zzzz:zzzz::1") is False

    def test_invalid_ipv6_multiple_double_colons(self):
        """Test addresses with multiple :: separators."""
        assert is_ipv6("2001::db8::1") is False

    def test_invalid_ipv6_incomplete(self):
        """Test incomplete addresses."""
        assert is_ipv6("2001:db8:") is False
        assert is_ipv6(":2001:db8::1") is False

    def test_invalid_ipv6_empty_or_spaces(self):
        """Test empty or whitespace strings."""
        assert is_ipv6("") is False
        assert is_ipv6(" ") is False
        assert is_ipv6("   ") is False

    def test_invalid_ipv6_ipv4_addresses(self):
        """Test that IPv4 addresses are not valid IPv6."""
        assert is_ipv6("192.168.1.1") is False
        assert is_ipv6("10.0.0.1") is False
        assert is_ipv6("127.0.0.1") is False

    def test_invalid_ipv6_wrong_type(self):
        """Test with non-string types."""
        assert is_ipv6(123) is False
        assert is_ipv6(None) is False
        assert is_ipv6(["2001", "db8", "1"]) is False
        assert is_ipv6({"ip": "::1"}) is False


# ============================================================================
# Generic IP Validation Tests
# ============================================================================


class TestIsIP:
    """Test cases for is_ip() function (IPv4 or IPv6)."""

    def test_valid_ip_ipv4(self):
        """Test that valid IPv4 addresses return True."""
        assert is_ip("192.168.1.1") is True
        assert is_ip("10.0.0.1") is True
        assert is_ip("127.0.0.1") is True
        assert is_ip("8.8.8.8") is True

    def test_valid_ip_ipv6(self):
        """Test that valid IPv6 addresses return True."""
        assert is_ip("::1") is True
        assert is_ip("2001:db8::1") is True
        assert is_ip("fe80::1") is True
        assert is_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True

    def test_invalid_ip_malformed(self):
        """Test malformed addresses."""
        assert is_ip("not-an-ip") is False
        assert is_ip("256.1.1.1") is False
        assert is_ip("gggg::1") is False
        assert is_ip("192.168.1") is False

    def test_invalid_ip_empty_or_spaces(self):
        """Test empty or whitespace strings."""
        assert is_ip("") is False
        assert is_ip(" ") is False
        assert is_ip("   ") is False

    def test_invalid_ip_wrong_type(self):
        """Test with non-string types."""
        assert is_ip(123) is False
        assert is_ip(None) is False
        assert is_ip([]) is False
        assert is_ip({}) is False


# ============================================================================
# Integration and Edge Cases
# ============================================================================


class TestIPValidationEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_private_ip_ranges(self):
        """Test all private IP ranges."""
        # RFC 1918 private ranges
        private_ips = [
            "10.0.0.0",
            "10.255.255.255",
            "172.16.0.0",
            "172.31.255.255",
            "192.168.0.0",
            "192.168.255.255",
        ]
        for ip in private_ips:
            assert is_ipv4(ip) is True
            assert is_ip(ip) is True

    def test_special_ipv4_addresses(self):
        """Test special use IPv4 addresses."""
        # Loopback
        assert is_ipv4("127.0.0.1") is True

        # Broadcast
        assert is_ipv4("255.255.255.255") is True

        # Unspecified
        assert is_ipv4("0.0.0.0") is True

        # Link-local
        assert is_ipv4("169.254.0.1") is True

    def test_special_ipv6_addresses(self):
        """Test special use IPv6 addresses."""
        # Loopback
        assert is_ipv6("::1") is True

        # Unspecified
        assert is_ipv6("::") is True

        # Link-local
        assert is_ipv6("fe80::1") is True

        # Unique local
        assert is_ipv6("fc00::1") is True
        assert is_ipv6("fd00::1") is True

    def test_workflow_scenario_alert_filtering(self):
        """Test realistic workflow: filtering alerts by IP validity."""
        alerts = [
            {"ip": "192.168.1.1", "severity": "high"},
            {"ip": "invalid-ip", "severity": "medium"},
            {"ip": "2001:db8::1", "severity": "low"},
            {"ip": "256.1.1.1", "severity": "high"},
            {"ip": "::1", "severity": "medium"},
        ]

        # Filter to only valid IPs
        valid_alerts = [a for a in alerts if is_ip(a["ip"])]

        assert len(valid_alerts) == 3
        assert valid_alerts[0]["ip"] == "192.168.1.1"
        assert valid_alerts[1]["ip"] == "2001:db8::1"
        assert valid_alerts[2]["ip"] == "::1"

    def test_workflow_scenario_ip_type_detection(self):
        """Test realistic workflow: detect IP type."""
        ips = [
            "192.168.1.1",
            "2001:db8::1",
            "10.0.0.1",
            "::1",
            "invalid",
        ]

        ipv4_count = sum(1 for ip in ips if is_ipv4(ip))
        ipv6_count = sum(1 for ip in ips if is_ipv6(ip))
        invalid_count = sum(1 for ip in ips if not is_ip(ip))

        assert ipv4_count == 2
        assert ipv6_count == 2
        assert invalid_count == 1

    def test_workflow_scenario_mixed_ip_validation(self):
        """Test realistic workflow: validate mixed IP list."""
        log_entries = [
            {"src_ip": "192.168.1.100", "dst_ip": "8.8.8.8"},
            {"src_ip": "fe80::1", "dst_ip": "2001:db8::1"},
            {"src_ip": "10.0.0.1", "dst_ip": "invalid"},
        ]

        # Validate all IPs
        results = []
        for entry in log_entries:
            results.append(
                {
                    "src_valid": is_ip(entry["src_ip"]),
                    "dst_valid": is_ip(entry["dst_ip"]),
                    "src_type": "ipv4"
                    if is_ipv4(entry["src_ip"])
                    else "ipv6"
                    if is_ipv6(entry["src_ip"])
                    else "invalid",
                    "dst_type": "ipv4"
                    if is_ipv4(entry["dst_ip"])
                    else "ipv6"
                    if is_ipv6(entry["dst_ip"])
                    else "invalid",
                }
            )

        # First entry: both IPv4
        assert results[0]["src_valid"] is True
        assert results[0]["dst_valid"] is True
        assert results[0]["src_type"] == "ipv4"
        assert results[0]["dst_type"] == "ipv4"

        # Second entry: both IPv6
        assert results[1]["src_valid"] is True
        assert results[1]["dst_valid"] is True
        assert results[1]["src_type"] == "ipv6"
        assert results[1]["dst_type"] == "ipv6"

        # Third entry: src IPv4, dst invalid
        assert results[2]["src_valid"] is True
        assert results[2]["dst_valid"] is False
        assert results[2]["src_type"] == "ipv4"
        assert results[2]["dst_type"] == "invalid"
