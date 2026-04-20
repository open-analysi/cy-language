"""Tests for Time Arithmetic Functions."""

import pytest

from cy_language.native_functions import (
    add_duration,
    duration_between,
    format_duration,
    from_epoch,
    parse_duration,
    subtract_duration,
    timestamp_compare,
    to_epoch,
)

# ============================================================================
# Duration Parsing Tests
# ============================================================================


class TestParseDuration:
    """Test cases for parse_duration() function."""

    def test_parse_duration_hours(self):
        """Test parsing hours."""
        assert parse_duration("1h") == 3600.0
        assert parse_duration("2h") == 7200.0
        assert parse_duration("24h") == 86400.0

    def test_parse_duration_minutes(self):
        """Test parsing minutes."""
        assert parse_duration("1m") == 60.0
        assert parse_duration("30m") == 1800.0
        assert parse_duration("60m") == 3600.0

    def test_parse_duration_days(self):
        """Test parsing days."""
        assert parse_duration("1d") == 86400.0
        assert parse_duration("2d") == 172800.0
        assert parse_duration("7d") == 604800.0

    def test_parse_duration_weeks(self):
        """Test parsing weeks."""
        assert parse_duration("1w") == 604800.0
        assert parse_duration("2w") == 1209600.0

    def test_parse_duration_seconds(self):
        """Test parsing seconds."""
        assert parse_duration("1s") == 1.0
        assert parse_duration("60s") == 60.0
        assert parse_duration("3600s") == 3600.0

    def test_parse_duration_combined(self):
        """Test parsing combined durations."""
        assert parse_duration("1h30m") == 5400.0  # 1.5 hours
        assert parse_duration("2d12h") == 216000.0  # 2.5 days
        assert parse_duration("1w2d3h") == 788400.0  # 1 week + 2 days + 3 hours

    def test_parse_duration_case_insensitive(self):
        """Test case insensitivity."""
        assert parse_duration("1H") == 3600.0
        assert parse_duration("30M") == 1800.0
        assert parse_duration("1D") == 86400.0

    def test_parse_duration_invalid(self):
        """Test invalid duration formats."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration("invalid")

        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration("")

        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration("abc")

    def test_parse_duration_invalid_type(self):
        """Test passing non-string to parse_duration."""
        with pytest.raises(ValueError, match="requires string"):
            parse_duration(123)


# ============================================================================
# Add Duration Tests
# ============================================================================


class TestAddDuration:
    """Test cases for add_duration() function."""

    def test_add_duration_hours(self):
        """Test adding hours to timestamp."""
        result = add_duration("2025-10-31T14:30:00Z", "1h")
        assert result == "2025-10-31T15:30:00Z"

        result = add_duration("2025-10-31T14:30:00Z", "2h")
        assert result == "2025-10-31T16:30:00Z"

    def test_add_duration_minutes(self):
        """Test adding minutes to timestamp."""
        result = add_duration("2025-10-31T14:30:00Z", "30m")
        assert result == "2025-10-31T15:00:00Z"

        result = add_duration("2025-10-31T14:00:00Z", "45m")
        assert result == "2025-10-31T14:45:00Z"

    def test_add_duration_days(self):
        """Test adding days to timestamp."""
        result = add_duration("2025-10-31T14:30:00Z", "1d")
        assert result == "2025-11-01T14:30:00Z"

        result = add_duration("2025-10-31T14:30:00Z", "7d")
        assert result == "2025-11-07T14:30:00Z"

    def test_add_duration_combined(self):
        """Test adding combined durations."""
        result = add_duration("2025-10-31T14:00:00Z", "1h30m")
        assert result == "2025-10-31T15:30:00Z"

        result = add_duration("2025-10-31T00:00:00Z", "2d12h")
        assert result == "2025-11-02T12:00:00Z"

    def test_add_duration_timezone_preserved(self):
        """Test that timezone is preserved."""
        result = add_duration("2025-10-31T14:30:00-08:00", "1h")
        assert result == "2025-10-31T15:30:00-08:00"

        result = add_duration("2025-10-31T14:30:00+05:30", "2h")
        assert result == "2025-10-31T16:30:00+05:30"

    def test_add_duration_invalid_timestamp(self):
        """Test with invalid timestamp format."""
        with pytest.raises(ValueError, match="Invalid ISO 8601 timestamp"):
            add_duration("invalid", "1h")

    def test_add_duration_invalid_duration(self):
        """Test with invalid duration format."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            add_duration("2025-10-31T14:30:00Z", "invalid")

    def test_add_duration_invalid_types(self):
        """Test with invalid parameter types."""
        with pytest.raises(ValueError, match="timestamp must be string"):
            add_duration(123, "1h")

        with pytest.raises(ValueError, match="duration must be string"):
            add_duration("2025-10-31T14:30:00Z", 123)


# ============================================================================
# Subtract Duration Tests
# ============================================================================


class TestSubtractDuration:
    """Test cases for subtract_duration() function."""

    def test_subtract_duration_hours(self):
        """Test subtracting hours from timestamp."""
        result = subtract_duration("2025-10-31T14:30:00Z", "1h")
        assert result == "2025-10-31T13:30:00Z"

        result = subtract_duration("2025-10-31T14:30:00Z", "2h")
        assert result == "2025-10-31T12:30:00Z"

    def test_subtract_duration_minutes(self):
        """Test subtracting minutes from timestamp."""
        result = subtract_duration("2025-10-31T14:30:00Z", "30m")
        assert result == "2025-10-31T14:00:00Z"

        result = subtract_duration("2025-10-31T14:00:00Z", "45m")
        assert result == "2025-10-31T13:15:00Z"

    def test_subtract_duration_days(self):
        """Test subtracting days from timestamp."""
        result = subtract_duration("2025-10-31T14:30:00Z", "1d")
        assert result == "2025-10-30T14:30:00Z"

        result = subtract_duration("2025-11-07T14:30:00Z", "7d")
        assert result == "2025-10-31T14:30:00Z"

    def test_subtract_duration_combined(self):
        """Test subtracting combined durations."""
        result = subtract_duration("2025-10-31T15:30:00Z", "1h30m")
        assert result == "2025-10-31T14:00:00Z"

    def test_subtract_duration_timezone_preserved(self):
        """Test that timezone is preserved."""
        result = subtract_duration("2025-10-31T14:30:00-08:00", "1h")
        assert result == "2025-10-31T13:30:00-08:00"

    def test_subtract_duration_across_boundaries(self):
        """Test subtraction across day/month boundaries."""
        result = subtract_duration("2025-11-01T00:30:00Z", "1h")
        assert result == "2025-10-31T23:30:00Z"

        result = subtract_duration("2025-11-01T14:00:00Z", "2d")
        assert result == "2025-10-30T14:00:00Z"


# ============================================================================
# Duration Between Tests
# ============================================================================


class TestDurationBetween:
    """Test cases for duration_between() function."""

    def test_duration_between_same_day(self):
        """Test duration between timestamps on same day."""
        result = duration_between("2025-10-31T14:00:00Z", "2025-10-31T16:30:00Z")
        assert result == "2h30m"

    def test_duration_between_hours_only(self):
        """Test duration with only hours."""
        result = duration_between("2025-10-31T14:00:00Z", "2025-10-31T17:00:00Z")
        assert result == "3h"

    def test_duration_between_different_days(self):
        """Test duration between different days."""
        result = duration_between("2025-10-31T14:00:00Z", "2025-11-01T14:00:00Z")
        assert result == "1d"

    def test_duration_between_complex(self):
        """Test complex duration."""
        result = duration_between("2025-10-31T10:00:00Z", "2025-11-02T14:30:45Z")
        # 2 days, 4 hours, 30 minutes, 45 seconds
        assert result == "2d4h30m45s"

    def test_duration_between_negative(self):
        """Test negative duration (end before start)."""
        result = duration_between("2025-10-31T16:00:00Z", "2025-10-31T14:00:00Z")
        assert result == "-2h"

    def test_duration_between_timezone_aware(self):
        """Test with timezone-aware timestamps."""
        result = duration_between(
            "2025-10-31T14:00:00-08:00", "2025-10-31T16:00:00-08:00"
        )
        assert result == "2h"


# ============================================================================
# Format Duration Tests
# ============================================================================


class TestFormatDuration:
    """Test cases for format_duration() function."""

    def test_format_duration_hours(self):
        """Test formatting hours."""
        assert format_duration(3600) == "1h"
        assert format_duration(7200) == "2h"

    def test_format_duration_minutes(self):
        """Test formatting minutes."""
        assert format_duration(60) == "1m"
        assert format_duration(1800) == "30m"

    def test_format_duration_combined(self):
        """Test formatting combined durations."""
        assert format_duration(5400) == "1h30m"
        assert format_duration(90061) == "1d1h1m1s"

    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "0s"

    def test_format_duration_negative(self):
        """Test formatting negative duration."""
        assert format_duration(-3600) == "-1h"
        assert format_duration(-5400) == "-1h30m"

    def test_format_duration_weeks(self):
        """Test formatting weeks."""
        assert format_duration(604800) == "1w"
        assert format_duration(1209600) == "2w"

    def test_format_duration_invalid_type(self):
        """Test with invalid type."""
        with pytest.raises(ValueError, match="requires number"):
            format_duration("invalid")


# ============================================================================
# Timestamp Compare Tests
# ============================================================================


class TestTimestampCompare:
    """Test cases for timestamp_compare() function."""

    def test_timestamp_compare_less_than(self):
        """Test less than comparison."""
        assert (
            timestamp_compare("2025-10-31T14:00:00Z", "<", "2025-10-31T15:00:00Z")
            is True
        )

        assert (
            timestamp_compare("2025-10-31T15:00:00Z", "<", "2025-10-31T14:00:00Z")
            is False
        )

    def test_timestamp_compare_greater_than(self):
        """Test greater than comparison."""
        assert (
            timestamp_compare("2025-10-31T15:00:00Z", ">", "2025-10-31T14:00:00Z")
            is True
        )

        assert (
            timestamp_compare("2025-10-31T14:00:00Z", ">", "2025-10-31T15:00:00Z")
            is False
        )

    def test_timestamp_compare_equal(self):
        """Test equality comparison."""
        assert (
            timestamp_compare("2025-10-31T14:00:00Z", "==", "2025-10-31T14:00:00Z")
            is True
        )

        assert (
            timestamp_compare("2025-10-31T14:00:00Z", "==", "2025-10-31T15:00:00Z")
            is False
        )

    def test_timestamp_compare_not_equal(self):
        """Test not equal comparison."""
        assert (
            timestamp_compare("2025-10-31T14:00:00Z", "!=", "2025-10-31T15:00:00Z")
            is True
        )

        assert (
            timestamp_compare("2025-10-31T14:00:00Z", "!=", "2025-10-31T14:00:00Z")
            is False
        )

    def test_timestamp_compare_less_than_or_equal(self):
        """Test less than or equal comparison."""
        assert (
            timestamp_compare("2025-10-31T14:00:00Z", "<=", "2025-10-31T15:00:00Z")
            is True
        )

        assert (
            timestamp_compare("2025-10-31T14:00:00Z", "<=", "2025-10-31T14:00:00Z")
            is True
        )

    def test_timestamp_compare_greater_than_or_equal(self):
        """Test greater than or equal comparison."""
        assert (
            timestamp_compare("2025-10-31T15:00:00Z", ">=", "2025-10-31T14:00:00Z")
            is True
        )

        assert (
            timestamp_compare("2025-10-31T14:00:00Z", ">=", "2025-10-31T14:00:00Z")
            is True
        )

    def test_timestamp_compare_timezone_aware(self):
        """Test comparison with timezone-aware timestamps."""
        # Same absolute time, different representations
        assert (
            timestamp_compare("2025-10-31T14:00:00Z", "==", "2025-10-31T06:00:00-08:00")
            is True
        )

    def test_timestamp_compare_invalid_operator(self):
        """Test with invalid operator."""
        with pytest.raises(ValueError, match="invalid operator"):
            timestamp_compare("2025-10-31T14:00:00Z", "invalid", "2025-10-31T15:00:00Z")


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_add_subtract_round_trip(self):
        """Test that add and subtract are inverse operations."""
        original = "2025-10-31T14:30:00Z"
        after_add = add_duration(original, "1h")
        back_to_original = subtract_duration(after_add, "1h")
        assert back_to_original == original

    def test_duration_across_year_boundary(self):
        """Test duration arithmetic across year boundary."""
        result = add_duration("2025-12-31T23:00:00Z", "2h")
        assert result == "2026-01-01T01:00:00Z"

        result = subtract_duration("2026-01-01T01:00:00Z", "2h")
        assert result == "2025-12-31T23:00:00Z"

    def test_large_durations(self):
        """Test with large durations."""
        result = add_duration("2025-10-31T00:00:00Z", "4w")
        assert result == "2025-11-28T00:00:00Z"

        result = parse_duration("52w")  # 1 year worth of weeks
        assert result == 31449600.0

    def test_very_small_durations(self):
        """Test with very small durations."""
        result = add_duration("2025-10-31T14:30:00Z", "1s")
        assert result == "2025-10-31T14:30:01Z"

        result = subtract_duration("2025-10-31T14:30:01Z", "1s")
        assert result == "2025-10-31T14:30:00Z"

    def test_workflow_scenario_alert_age(self):
        """Test realistic workflow: check if alert is old."""
        alert_time = "2025-10-30T10:00:00Z"
        current_time = "2025-10-31T14:00:00Z"

        # Calculate age
        age_duration = duration_between(alert_time, current_time)
        age_seconds = parse_duration(age_duration)

        # Check if older than 24 hours
        threshold_seconds = parse_duration("24h")
        is_old = age_seconds > threshold_seconds

        assert is_old is True

    def test_workflow_scenario_time_window(self):
        """Test realistic workflow: filter by time window."""
        current_time = "2025-10-31T14:00:00Z"
        cutoff_time = subtract_duration(current_time, "15m")

        # Check if event is within window
        event_time = "2025-10-31T13:50:00Z"
        is_recent = timestamp_compare(event_time, ">", cutoff_time)

        assert is_recent is True

    def test_workflow_scenario_sla_breach(self):
        """Test realistic workflow: SLA breach detection."""
        incident_created = "2025-10-31T10:00:00Z"
        sla_deadline = add_duration(incident_created, "4h")
        current_time = "2025-10-31T15:00:00Z"

        # Check if SLA breached
        breached = timestamp_compare(current_time, ">", sla_deadline)
        assert breached is True

        # Calculate how much over
        if breached:
            time_over = duration_between(sla_deadline, current_time)
            assert time_over == "1h"

    def test_multiple_unit_parsing(self):
        """Test parsing multiple units in single duration string."""
        result = parse_duration("1w2d3h4m5s")
        # 1 week + 2 days + 3 hours + 4 minutes + 5 seconds
        expected = (7 * 24 * 3600) + (2 * 24 * 3600) + (3 * 3600) + (4 * 60) + 5
        assert result == expected

    def test_duration_format_precision(self):
        """Test duration formatting includes all units."""
        # 1 day, 2 hours, 3 minutes, 4 seconds
        seconds = (1 * 86400) + (2 * 3600) + (3 * 60) + 4
        result = format_duration(seconds)
        assert result == "1d2h3m4s"


# ============================================================================
# Epoch Conversion Tests
# ============================================================================


class TestEpochConversion:
    """Test cases for from_epoch() and to_epoch() functions."""

    def test_from_epoch_basic(self):
        """Test basic epoch to ISO 8601 conversion."""
        # Known epoch timestamp: June 15, 2023 14:30:32 UTC
        result = from_epoch(1686839432)
        assert result == "2023-06-15T14:30:32Z"

    def test_from_epoch_zero(self):
        """Test epoch 0 (Unix epoch start)."""
        result = from_epoch(0)
        assert result == "1970-01-01T00:00:00Z"

    def test_from_epoch_with_timezone(self):
        """Test epoch conversion with timezone."""
        # Same epoch, different timezone (June 15, 2023)
        result_utc = from_epoch(1686839432, "UTC")
        result_pst = from_epoch(1686839432, "US/Pacific")

        assert result_utc == "2023-06-15T14:30:32Z"
        assert result_pst == "2023-06-15T07:30:32-07:00"  # 7 hours behind UTC (PDT)

    def test_from_epoch_float(self):
        """Test epoch with fractional seconds."""
        result = from_epoch(1686839432.5)
        # Should handle fractional seconds (June 15, 2023)
        assert "2023-06-15T14:30:32" in result

    def test_from_epoch_negative(self):
        """Test negative epoch (before 1970)."""
        result = from_epoch(-86400)  # 1 day before epoch
        assert result == "1969-12-31T00:00:00Z"

    def test_from_epoch_invalid_type(self):
        """Test with invalid type."""
        with pytest.raises(ValueError, match="seconds must be number"):
            from_epoch("not a number")

    def test_from_epoch_invalid_timezone(self):
        """Test with invalid timezone."""
        with pytest.raises(ValueError, match="Invalid timezone"):
            from_epoch(1686839432, "Invalid/Timezone")

    def test_to_epoch_basic(self):
        """Test basic ISO 8601 to epoch conversion."""
        result = to_epoch("2023-06-15T14:30:32Z")
        assert result == 1686839432.0

    def test_to_epoch_zero(self):
        """Test Unix epoch start."""
        result = to_epoch("1970-01-01T00:00:00Z")
        assert result == 0.0

    def test_to_epoch_with_timezone(self):
        """Test that different timezones convert to same epoch."""
        epoch_utc = to_epoch("2023-06-15T14:30:32Z")
        epoch_pst = to_epoch("2023-06-15T07:30:32-07:00")

        # Same absolute time, different representations (June 15 = PDT = -07:00)
        assert epoch_utc == epoch_pst
        assert epoch_utc == 1686839432.0

    def test_to_epoch_negative(self):
        """Test timestamp before Unix epoch."""
        result = to_epoch("1969-12-31T00:00:00Z")
        assert result == -86400.0

    def test_to_epoch_invalid_timestamp(self):
        """Test with invalid timestamp format."""
        with pytest.raises(ValueError, match="Invalid ISO 8601 timestamp"):
            to_epoch("not a timestamp")

    def test_to_epoch_invalid_type(self):
        """Test with invalid type."""
        with pytest.raises(ValueError, match="requires string"):
            to_epoch(1234567890)

    def test_epoch_round_trip(self):
        """Test converting to epoch and back."""
        original = "2023-06-15T14:30:32Z"
        epoch = to_epoch(original)
        back_to_iso = from_epoch(epoch)

        assert back_to_iso == original

    def test_epoch_round_trip_with_timezone(self):
        """Test round trip with timezone."""
        original_pst = "2023-06-15T07:30:32-07:00"  # June = PDT = -07:00
        epoch = to_epoch(original_pst)
        back_to_pst = from_epoch(epoch, "US/Pacific")

        assert back_to_pst == original_pst

    def test_epoch_workflow_api_timestamp(self):
        """Test realistic workflow: API returns epoch timestamp."""
        # Simulate API returning epoch timestamp (June 15, 2023)
        api_timestamp = 1686839432

        # Convert to ISO 8601 for Cy processing
        iso_timestamp = from_epoch(api_timestamp)

        # Use in time arithmetic
        one_hour_later = add_duration(iso_timestamp, "1h")

        # Convert back to epoch if needed
        epoch_result = to_epoch(one_hour_later)

        assert epoch_result == api_timestamp + 3600  # 1 hour = 3600 seconds

    def test_epoch_workflow_log_timestamps(self):
        """Test realistic workflow: Working with log timestamps."""
        # Splunk-style epoch timestamps (June 15, 2023)
        log_entries = [
            {"message": "Error occurred", "timestamp": 1686839432},
            {
                "message": "Recovery started",
                "timestamp": 1686839492,
            },  # 60 seconds later
        ]

        # Convert to ISO 8601 for comparison
        error_time = from_epoch(log_entries[0]["timestamp"])
        recovery_time = from_epoch(log_entries[1]["timestamp"])

        # Calculate duration between events
        duration = duration_between(error_time, recovery_time)

        assert duration == "1m"  # 60 seconds = 1 minute
