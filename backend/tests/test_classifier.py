from app.etl.classifier import classify_type, detect_indexing, extract_topics


def test_classifies_call_for_papers():
    text = "Call for Papers: submit your extended abstract by March 1."
    assert classify_type(text) == "CALL_FOR_PAPER"


def test_classifies_grant():
    text = "DOST-NRCP Grants-in-Aid Program: apply for research funding."
    assert classify_type(text) == "GRANT"


def test_classifies_call_for_publication():
    text = "Call for Publication: submit manuscripts for the special issue."
    assert classify_type(text) == "CALL_FOR_PAPER"


def test_classifies_special_issue_as_call_for_paper():
    text = "Special issue on AI in public health now open for submissions."
    assert classify_type(text) == "CALL_FOR_PAPER"


def test_classifies_call_for_proposal_as_grant():
    text = "Call for Proposals: DOST-PCIEERD funding opportunity for 2026."
    assert classify_type(text) == "GRANT"


def test_out_of_scope_text_returns_none():
    """Anything that isn't clearly a call for papers or a grant is out of
    scope for this system — conferences, fellowships, scholarships,
    startup challenges, trainings, etc. all fall here now."""
    text = "Join the University Robotics Challenge this semester."
    assert classify_type(text) is None


def test_default_classification_is_none():
    assert classify_type("Nothing matches any keyword here.") is None


def test_extract_topics_finds_known_vocabulary():
    text = "A startup challenge on fintech and artificial intelligence for SMEs."
    topics = extract_topics(text)
    assert "fintech" in topics
    assert "artificial intelligence" in topics
    assert "startup" in topics


def test_extract_topics_finds_spinoff_vocabulary():
    text = "Technology transfer office supports spin-off commercialization."
    topics = extract_topics(text)
    assert "technology transfer" in topics
    assert "spin-off" in topics
    assert "commercialization" in topics


def test_detect_indexing_finds_scopus_and_wos_together():
    text = "Call for Publication: Scopus and Web of Science indexed journal."
    flags = detect_indexing(text)
    assert "SCOPUS" in flags
    assert "WEB_OF_SCIENCE" in flags


def test_detect_indexing_recognizes_clarivate_and_isi_as_web_of_science():
    text = "Manuscripts accepted for this Clarivate ISI-indexed journal."
    assert detect_indexing(text) == ["WEB_OF_SCIENCE"]


def test_detect_indexing_returns_empty_when_nothing_stated():
    text = "Call for Papers: submit your abstract by March 1."
    assert detect_indexing(text) == []


def test_detect_indexing_finds_ched_accredited_and_peer_reviewed():
    text = "Publish in this CHED accredited journal, a peer-reviewed journal."
    flags = detect_indexing(text)
    assert "CHED_ACCREDITED" in flags
    assert "PEER_REVIEWED" in flags
