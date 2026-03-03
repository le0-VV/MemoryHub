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

    def test_naive_datetime_interprets_as_local_time(self):
        """Naive datetimes should be treated as local time in the fork."""
        naive_dt = datetime(2024, 1, 15, 12, 30, 0)
        result = ensure_timezone_aware(naive_dt)

        assert result.tzinfo is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30

    def test_naive_datetime_preserves_wall_clock_fields(self):
        """Local timezone attachment should not rewrite the original wall clock fields."""
        naive_dt = datetime(2024, 6, 15, 18, 0, 0)  # Summer time
        result = ensure_timezone_aware(naive_dt)

        assert result.hour == 18
        assert result.minute == 0
        assert result.tzinfo is not None

    def test_naive_datetime_does_not_require_mode_selection(self):
        """The helper should work without any cloud/local branching inputs."""
        naive_dt = datetime(2024, 1, 15, 12, 30, 0)
        result = ensure_timezone_aware(naive_dt)

        assert result.tzinfo is not None

    def test_timezone_aware_local_datetime_is_returned_unchanged(self):
        """Already-aware local datetimes should pass through unchanged."""
        local_dt = datetime.now().astimezone().replace(
            year=2024,
            month=1,
            day=15,
            hour=18,
            minute=30,
            second=0,
            microsecond=0,
        )

        result = ensure_timezone_aware(local_dt)
        assert result == local_dt
        assert result.hour == 18
