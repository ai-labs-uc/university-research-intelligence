from app.etl.collector import discover_links

SAMPLE_HTML = """
<html><body>
  <a href="/calls/ai-research-grant">Call for Proposals: AI Research Grant</a>
  <a href="/about">About Us</a>
  <a href="/calls/robotics-hackathon">Robotics Hackathon 2026</a>
  <a href="https://external-site.example/other">Off-site link</a>
</body></html>
"""

WIKICFP_STYLE_HTML = """
<html><body>
  <a href="/cfp/servlet/event.showcfp?eventid=1">ICML 2027</a>
  <a href="/cfp/servlet/event.showcfp?eventid=2">NeurIPS 2027</a>
  <a href="/about">About WikiCFP</a>
</body></html>
"""


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def test_discover_links_filters_by_keyword(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        return FakeResponse(SAMPLE_HTML)

    monkeypatch.setattr("app.etl.collector.requests.get", fake_get)

    source = {
        "listing_url": "https://example.gov.ph/announcements/",
        "keywords": ["call for proposal"],
    }
    links = discover_links(source)

    assert any("ai-research-grant" in link for link in links)
    assert not any("robotics-hackathon" in link for link in links)
    assert not any("about" in link for link in links)
    # off-site links are always excluded regardless of keywords
    assert not any("external-site.example" in link for link in links)


def test_discover_links_takes_everything_when_keywords_empty(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        return FakeResponse(WIKICFP_STYLE_HTML)

    monkeypatch.setattr("app.etl.collector.requests.get", fake_get)

    source = {
        "listing_url": "http://www.wikicfp.com/cfp/",
        "keywords": [],
    }
    links = discover_links(source)

    # link text is just conference names, not "call for papers" — an
    # empty keyword list must still pick these up
    assert any("eventid=1" in link for link in links)
    assert any("eventid=2" in link for link in links)
    assert any("about" in link for link in links)
