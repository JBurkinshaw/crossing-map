"""The drafted action for a reservoir, by its dam's year (decision 0031)."""

import sys

import pytest

from crossing.paths import REPO

# The tiles package sits at the repository root, beside pipeline/.
sys.path.insert(0, str(REPO))
from tiles import later_reservoirs  # noqa: E402


def props(year: int | None, lake_ctrl: str | None = None) -> dict:
    return {"YEAR_DAM": year, "LAKE_CTRL": lake_ctrl}


@pytest.mark.parametrize(("year", "lake_ctrl", "action"), [
    (1964, None, "drop"),
    (1946, None, "drop"),
    (1945, None, "keep"),
    (1942, None, "keep"),
    (1911, None, "keep"),
    (-99, None, "keep"),
    (None, None, "keep"),
    (1970, "Yes", "keep"),
])
def test_drafted_action(year, lake_ctrl, action):
    assert later_reservoirs.drafted(props(year, lake_ctrl))[0] == action


def test_no_year_and_lake_control_ask_for_review():
    assert later_reservoirs.drafted(props(-99))[1].startswith("Review")
    assert later_reservoirs.drafted(props(1970, "Yes"))[1].startswith("Review")
