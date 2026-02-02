from app.modules.crisis_detector import crisis_detector

def test_no_crisis():
    text = "I am feeling a bit sad today but I went for a walk."
    is_crisis, severity, response, flags = crisis_detector.detect(text)
    assert is_crisis is False
    assert severity < 7
    assert response is None

def test_high_severity_keyword():
    text = "I want to kill myself"
    is_crisis, severity, response, flags = crisis_detector.detect(text)
    assert is_crisis is True
    assert severity >= 9
    assert response is not None
    assert "NIMHANS" in response

def test_pattern_matching():
    text = "i am going to end it all tonight"
    is_crisis, severity, response, flags = crisis_detector.detect(text)
    assert is_crisis is True
    assert severity >= 10
    assert response is not None

def test_moderate_distress():
    text = "I feel hopeless and worthless lately."
    is_crisis, severity, response, flags = crisis_detector.detect(text)
    # Severity for 'hopeless' is 5, 'worthless' is 5. Should be approx 5.
    # Should NOT trigger hard block (is_crisis = False), but will pass severity info to LLM.
    assert is_crisis is False 
    assert severity >= 5
    assert severity < 7
    assert response is None
