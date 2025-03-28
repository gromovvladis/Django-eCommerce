import pytest
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.db.models import Sum, F
from django.db.models.functions import Coalesce


class TestKitchenFunctions(TestCase):
    def setUp(self):
        self.timezone = ZoneInfo("Europe/Moscow")
        self.current_time = datetime.now(tz=self.timezone)
        self.store = MagicMock()
        self.basket = MagicMock()
        self.basket.store = self.store
        self.basket.store.start_worktime = time(9, 0)
        self.basket.store.end_worktime = time(21, 0)

    @patch("django.conf.settings.ORDER_BUSY_STATUSES", ["preparing", "cooking"])
    @patch("your_app.models.Order.objects.filter")
    def test_kitchen_busy(self, mock_filter):
        # Mock data setup
        order1 = MagicMock()
        order1.order_time = self.current_time + timedelta(minutes=30)
        order1.total_cooking_time = 15

        order2 = MagicMock()
        order2.order_time = self.current_time - timedelta(
            minutes=30
        )  # Should be filtered out
        order2.total_cooking_time = 10

        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value.order_by.return_value.only.return_value = [
            order1
        ]
        mock_filter.return_value = mock_queryset

        # Test
        result = kitchen_busy(self.store)

        # Assertions
        expected_start = order1.order_time - timedelta(minutes=15)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (expected_start, order1.order_time))
        mock_filter.assert_called_with(
            status__in=["preparing", "cooking"], store=self.store
        )

    @patch("your_app.models.Order.objects.filter")
    def test_kitchen_busy_empty(self, mock_filter):
        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value.order_by.return_value.only.return_value = []
        mock_filter.return_value = mock_queryset

        result = kitchen_busy(self.store)
        self.assertEqual(result, [])

    @patch("your_app.kitchen_busy")
    @patch("your_app.models.Basket.lines.aggregate")
    def test_pickup_now_finds_slot(self, mock_aggregate, mock_kitchen_busy):
        # Setup test data
        mock_aggregate.return_value = {"cooking_time_sum": 30}

        # Mock kitchen_busy to return one busy period
        busy_start = self.current_time.replace(hour=10, minute=0)
        busy_end = busy_start + timedelta(minutes=45)
        mock_kitchen_busy.return_value = [(busy_start, busy_end)]

        # Test - should find slot after busy period
        result = pickup_now(self.basket)
        expected_time = busy_end + timedelta(minutes=30)
        self.assertEqual(result, expected_time)

    @patch("your_app.kitchen_busy")
    @patch("your_app.models.Basket.lines.aggregate")
    def test_pickup_now_full_day(self, mock_aggregate, mock_kitchen_busy):
        mock_aggregate.return_value = {"cooking_time_sum": 30}

        # Mock completely busy day
        work_start = datetime.combine(self.current_time.date(), time(9, 0)).replace(
            tzinfo=self.timezone
        )
        work_end = datetime.combine(self.current_time.date(), time(21, 0)).replace(
            tzinfo=self.timezone
        )
        mock_kitchen_busy.return_value = [(work_start, work_end)]

        # Test - should try next day
        with patch("your_app.datetime") as mock_datetime:
            mock_datetime.now.return_value = self.current_time
            mock_datetime.combine.side_effect = datetime.combine
            result = pickup_now(self.basket)

            # Should return first available time next day
            expected_time = datetime.combine(
                self.current_time.date() + timedelta(days=1), time(9, 0)
            ).replace(tzinfo=self.timezone) + timedelta(minutes=30)

            self.assertEqual(result, expected_time)

    @patch("your_app.kitchen_busy")
    @patch("your_app.models.Basket.lines.aggregate")
    def test_pickup_now_no_available_slots(self, mock_aggregate, mock_kitchen_busy):
        mock_aggregate.return_value = {"cooking_time_sum": 30}

        # Mock completely busy week
        work_start = datetime.combine(self.current_time.date(), time(9, 0)).replace(
            tzinfo=self.timezone
        )
        work_end = datetime.combine(
            self.current_time.date() + timedelta(days=6), time(21, 0)
        ).replace(tzinfo=self.timezone)
        mock_kitchen_busy.return_value = [(work_start, work_end)]

        result = pickup_now(self.basket)
        self.assertIsNone(result)

    def test_pickup_now_edge_cases(self):
        # Test with empty basket
        empty_basket = MagicMock()
        empty_basket.store = self.store
        empty_basket.lines.aggregate.return_value = {"cooking_time_sum": None}

        with patch("your_app.kitchen_busy", return_value=[]):
            result = pickup_now(empty_basket)
            expected_time = max(
                datetime.now(tz=self.timezone),
                datetime.combine(datetime.now().date(), time(9, 0)).replace(
                    tzinfo=self.timezone
                ),
            ) + timedelta(minutes=0)

            self.assertEqual(result, expected_time)
