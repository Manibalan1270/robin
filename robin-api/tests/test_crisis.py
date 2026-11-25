import pytest

from app.modules.crisis_detector import crisis_detector


def test_no_crisis():
    is_crisis, severity, response, _ = crisis_detector.detect("I am feeling a bit sad today but I went for a walk.")
    assert is_crisis is False
    assert severity < 7
    assert response is None


def test_high_severity_keyword():
    is_crisis, severity, response, _ = crisis_detector.detect("I want to kill myself")
    assert is_crisis is True
    assert severity >= 9
    assert "14416" in response


def test_pattern_matching():
    is_crisis, severity, response, _ = crisis_detector.detect("i am going to end it all tonight")
    assert is_crisis is True
    assert severity >= 9
    assert response is not None


def test_moderate_distress():
    is_crisis, severity, response, _ = crisis_detector.detect("I feel hopeless and worthless lately.")
    assert is_crisis is False
    assert 5 <= severity < 7
    assert response is None


@pytest.mark.parametrize(
    "text",
    [
        "I wanna end it",
        "nobody would miss me if I was gone",
        "everyone would be better off without me",
        "i want to k1ll myself",
        "I don't want to live anymore",
        "thinking about suicide",
        "I've been cutting myself",
    ],
)
def test_detects_other_phrasings(text):
    assert crisis_detector.detect(text)[0] is True


@pytest.mark.parametrize(
    "text",
    [
        "I studied for my diet exam",
        "learning a new skill",
        "the battery died",
        "I'm going to die of embarrassment lol",
        "this song is killing it",
    ],
)
def test_no_false_alarm_on_everyday_words(text):
    is_crisis, severity, _, _ = crisis_detector.detect(text)
    assert is_crisis is False
    assert severity < 5
