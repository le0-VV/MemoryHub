"""Tests for timezone utilities."""

from datetime import datetime, timezone

from memoryhub.utils import ensure_timezone_aware


class TestEnsureTimezoneAware:
    """Tests for ensure_timezone_aware function."""

    def test_already_timezone_aware_returns_unchanged(self):
        """Timezone-aware datetime should be returned unchanged."""
        dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        result = ensure_timezone_aware(dt)
        assert result == dt
        assert result.tzinfo == timezone.utc

    def test_naive_datetime_legacy_utc_mode_interprets_as_utc(self):
        """Legacy UTC compatibility mode should tag naive datetimes as UTC."""
        naive_dt = datetime(2024, 1, 15, 12, 30, 0)
        result = ensure_timezone_aware(naive_dt, cloud_mode=True)

        # Should have UTC timezone
        assert result.tzinfo == timezone.utc
        # Time values should be unchanged (just tagged as UTC)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30

    def test_naive_datetime_local_mode_interprets_as_local(self):
        """In local mode, naive datetimes should be interpreted as local time."""
        naive_dt = datetime(2024, 1, 15, 12, 30, 0)
        result = ensure_timezone_aware(naive_dt, cloud_mode=False)

        # Should have some timezone info (local)
        assert result.tzinfo is not None
        # The datetime should be converted to local timezone
        # We can't assert exact timezone as it depends on system

    def test_legacy_utc_mode_does_not_shift_time(self):
        """Legacy UTC mode should use replace() so time values stay unchanged."""
        naive_dt = datetime(2024, 6, 15, 18, 0, 0)  # Summer time
        result = ensure_timezone_aware(naive_dt, cloud_mode=True)

        # Hour should remain 18, not be shifted by timezone offset
        assert result.hour == 18
        assert result.tzinfo == timezone.utc

    def test_explicit_mode_skips_config_loading(self):
        """Explicit mode flags should not need config lookup."""
        naive_dt = datetime(2024, 1, 15, 12, 30, 0)

        # Should work without any config setup
        result_cloud = ensure_timezone_aware(naive_dt, cloud_mode=True)
        assert result_cloud.tzinfo == timezone.utc

        result_local = ensure_timezone_aware(naive_dt, cloud_mode=False)
        assert result_local.tzinfo is not None

    def test_none_cloud_mode_defaults_to_local_semantics(self, config_manager):
        """Omitting the flag should keep the local SQLite default."""
        naive_dt = datetime(2024, 1, 15, 12, 30, 0)

        result = ensure_timezone_aware(naive_dt, cloud_mode=None)

        assert result.tzinfo is not None

    def test_legacy_utc_mode_preserves_old_asyncpg_timestamp_interpretation(self):
        """Compatibility flag should preserve old UTC-tagging behavior."""
        legacy_value = datetime(2024, 1, 15, 18, 30, 0)

        result = ensure_timezone_aware(legacy_value, cloud_mode=True)
        assert result == datetime(2024, 1, 15, 18, 30, 0, tzinfo=timezone.utc)
        assert result.hour == 18
