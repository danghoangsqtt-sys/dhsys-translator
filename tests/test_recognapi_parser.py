import pytest

from videotrans.configure.excepts import SpeechToTextError
from videotrans.recognition._recognapi import (
    MAX_VIBEVOICE_RESPONSE_CHARS,
    MAX_VIBEVOICE_SEGMENTS,
    _parse_vibevoice_segments,
)


def test_parses_json_with_gradio_wrapper():
    raw = 'Transcript:\n[{"Start": 0, "End": 1.25, "Content": "Hello", "Speaker": "Speaker 1"}]\nDone'
    assert _parse_vibevoice_segments(raw) == [
        {"Start": 0.0, "End": 1.25, "Content": "Hello", "Speaker": "Speaker 1"}
    ]


def test_parses_legacy_python_literal():
    raw = "[{'Start': '1', 'End': '2', 'Content': 'Hello', 'Speaker': 'Speaker 1'}]"
    assert _parse_vibevoice_segments(raw)[0]["End"] == 2.0


@pytest.mark.parametrize("raw", [
    '[{"Start": 2, "End": 1, "Content": "bad"}]',
    '[{"Start": -1, "End": 1, "Content": "bad"}]',
    '[{"Start": NaN, "End": 1, "Content": "bad"}]',
    '[{"Start": 0, "End": 1, "Content": 123}]',
    '[{"Start": 0, "End": 1, "Content": "ok", "Speaker": 123}]',
    '[{"Start": 0, "End": 1}]',
    '[42]',
])
def test_rejects_invalid_segments(raw):
    with pytest.raises(SpeechToTextError):
        _parse_vibevoice_segments(raw)


def test_does_not_execute_expression(tmp_path):
    target = tmp_path / "executed.txt"
    raw = "[{'Start': 0, 'End': 1, 'Content': __import__('pathlib').Path(%r).write_text('bad')}]" % str(target)
    with pytest.raises(SpeechToTextError):
        _parse_vibevoice_segments(raw)
    assert not target.exists()


def test_bounds_response_and_segment_count():
    with pytest.raises(SpeechToTextError, match="too large"):
        _parse_vibevoice_segments("x" * (MAX_VIBEVOICE_RESPONSE_CHARS + 1))
    with pytest.raises(SpeechToTextError, match="segment count"):
        _parse_vibevoice_segments("[" + ",".join(
            '{"Start":0,"End":1,"Content":"x"}' for _ in range(MAX_VIBEVOICE_SEGMENTS + 1)
        ) + "]")
