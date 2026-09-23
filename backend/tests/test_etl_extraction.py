"""
Regression tests for the three defects that broke this system in production.

1. Deadlines were never extracted, so every row had deadline = NULL and
   no deadline notification could ever fire.
2. Navigation links were stored as opportunities ("Submission Policies",
   "Become an IEEE Conference Author").
3. opportunity_type received values outside its ENUM, and scope_type was
   given the opportunity type instead of NATIONAL/INTERNATIONAL.

Run:  cd backend && python -m pytest tests/test_etl_extraction.py -v
"""

from datetime import date

import pytest

from app.etl.classifier import classify
from app.etl.dates import derive_status, extract_deadline, extract_opening_date
from app.etl.filters import (
    detect_indexing,
    has_call_signal,
    looks_like_navigation,
    strip_boilerplate,
)

REFERENCE_DAY = date(2026, 9, 22)


# ----------------------------------------------------------------------
# 1. Deadline extraction
# ----------------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    # Phrasings taken from real PH agency and publisher pages
    ("Submission deadline 31 Jul 2027", date(2027, 7, 31)),
    ("Deadline for the submission of proposals is 15 October 2026.",
     date(2026, 10, 15)),
    ("Interested applicants must submit on or before November 30, 2026.",
     date(2026, 11, 30)),
    ("Closing date: 22 December 2026 4:00pm UK time", date(2026, 12, 22)),
    ("Proposals are due on 2027-01-15.", date(2027, 1, 15)),
    ("Deadline of submission: 05/12/2026", date(2026, 12, 5)),
    ("Papers must be submitted not later than Feb. 28, 2027",
     date(2027, 2, 28)),
    ("Application deadline 1 March 2027", date(2027, 3, 1)),
    ("The call closes on 30 Sept 2026", date(2026, 9, 30)),
    ("15 November 2026 is the deadline for abstracts", date(2026, 11, 15)),
    ("Abstract submission deadline: 10 Jan 2027", date(2027, 1, 10)),
])
def test_extracts_real_deadlines(text, expected):
    assert extract_deadline(text, not_before=REFERENCE_DAY) == expected


@pytest.mark.parametrize("text", [
    "Published: 12 March 2024. General news about the agency.",
    "Opening date: 1 October 2026",
    "Posted on 5 May 2026 by the communications office",
    "Submission deadline was 1 January 2020",   # expired -> previous cycle
    "No dates mentioned anywhere in this announcement.",
])
def test_rejects_non_deadlines(text):
    assert extract_deadline(text, not_before=REFERENCE_DAY) is None


def test_opening_date_allows_past_dates():
    assert extract_opening_date("Opening date: 1 August 2026") == date(2026, 8, 1)


def test_status_derives_from_dates():
    assert derive_status(date(2099, 1, 1)) == "OPEN"
    assert derive_status(date(2000, 1, 1)) == "CLOSED"
    assert derive_status(None) == "UNKNOWN"


# ----------------------------------------------------------------------
# 2. Navigation filtering
# ----------------------------------------------------------------------
@pytest.mark.parametrize("title", [
    "Become an IEEE Conference Author",   # actually stored in production
    "Submission Policies",                # actually stored in production
    "Publish with IEEE Conferences",      # actually stored in production
    "Home",
    "Privacy Policy",
    "Login",
    "Transparency Seal",
])
def test_rejects_navigation_titles(title):
    assert looks_like_navigation(title) is True


@pytest.mark.parametrize("title", [
    "Call for Proposals: 2027 UP CIDS Policy Research Project Grant",
    "Call for Proposals for the 2026 DOST-JSPS Joint Research Project",
    "Special Issue on Sustainable Agriculture in Southeast Asia",
])
def test_keeps_real_opportunity_titles(title):
    assert looks_like_navigation(title) is False


@pytest.mark.parametrize("text,expected", [
    ("Call for Papers: 8th Katipunan Conference", True),
    ("Request for Proposals - Basic Research Grant", True),
    ("Special Issue: Machine Learning in Healthcare", True),
    ("DOST holds annual sportsfest in Bicol", False),
    ("Agency announces new office hours", False),
])
def test_call_signal(text, expected):
    assert bool(has_call_signal(text)) is expected


def test_strips_boilerplate_but_keeps_content():
    dirty = (
        "Skip to main content More IEEE sites IEEE.org IEEE Xplore\n"
        "This site uses cookies.\n"
        "Call for Papers on quantum networks."
    )
    clean = strip_boilerplate(dirty)
    assert "Skip to main content" not in clean
    assert "cookies" not in clean
    assert "quantum networks" in clean


# ----------------------------------------------------------------------
# 3. Classification: type vs scope vs category
# ----------------------------------------------------------------------
def test_grant_classification_is_enum_safe():
    result = classify(
        "Call for Proposals: Basic Research Grants-in-Aid 2027",
        "DOST invites proposals. Deadline 30 November 2026.",
        {"name": "DOST-PCIEERD", "scope": "NATIONAL"},
    )
    # opportunity_type must stay inside ENUM('GRANT','CALL_FOR_PAPER').
    assert result["opportunity_type"] == "GRANT"
    # scope_type must be a scope, not a copy of the type.
    assert result["scope_type"] == "NATIONAL"
    assert result["category"] == "GRANT_PHILIPPINES"


def test_international_cfp_classification():
    result = classify(
        "Special Issue: Sustainable Urban Systems — Call for Papers",
        "Submission deadline 31 Jul 2027. Indexed in Scopus.",
        {"name": "MDPI Sustainability", "scope": "INTERNATIONAL"},
    )
    assert result["opportunity_type"] == "CALL_FOR_PAPER"
    assert result["scope_type"] == "INTERNATIONAL"
    assert result["category"] == "CALL_FOR_PAPER_INTERNATIONAL"


@pytest.mark.parametrize("title,body", [
    ("Submission Policies", "General author guidance."),
    ("DOST holds annual sportsfest", "Sports news from the agency."),
    ("About Us", "Information about the organisation."),
])
def test_non_opportunities_are_skipped(title, body):
    assert classify(title, body, {"name": "X"}) is None


def test_indexing_is_read_not_inferred():
    assert "SCOPUS" in detect_indexing("This journal is indexed in Scopus.")
    assert "WEB_OF_SCIENCE" in detect_indexing("Listed in Web of Science.")
    # A well-known publisher name alone must NOT imply indexing.
    assert detect_indexing("Published by Springer Nature.") == []
