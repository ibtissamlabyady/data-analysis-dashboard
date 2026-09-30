import unittest
from datetime import date

from streamlit.testing.v1 import AppTest

from src.analytics import ROOT


class AppTests(unittest.TestCase):
    def test_filter_empty_state_and_reset(self):
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=20).run()
        self.assertFalse(app.exception)
        initial = app.metric[0].value
        app.multiselect(key="regions").set_value(["North"]).run()
        self.assertFalse(app.exception)
        self.assertNotEqual(app.metric[0].value, initial)
        orders = app.dataframe[1].value
        self.assertEqual(set(orders["region"]), {"North"})
        app.multiselect(key="regions").set_value([]).run()
        self.assertFalse(app.exception)
        self.assertIn("No orders match", app.info[0].value)
        app.button[0].click().run()
        self.assertEqual(app.metric[0].value, initial)
        self.assertFalse(app.exception)

    def test_partial_date_and_unavailable_comparison(self):
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=20).run()
        app.date_input(key="dates").set_value((date(2025, 1, 1),)).run()
        self.assertFalse(app.exception)
        self.assertIn("Select an end date", app.info[0].value)
        app.date_input(key="dates").set_value((date(2024, 1, 1), date(2024, 1, 31))).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Prior-period changes are unavailable" in c.value for c in app.caption))
        self.assertEqual(app.metric[0].delta, "")


if __name__ == "__main__":
    unittest.main()
