from videotrans.recognition._base import BaseRecogn
from videotrans.task.taskcfg import SrtItem
from videotrans.configure.config import settings


def _make_srt(text, start, end, line=1):
    return SrtItem(
        text=text, start_time=start, end_time=end,
        startraw=f"00:00:{start // 1000:02d},{start % 1000:03d}",
        endraw=f"00:00:{end // 1000:02d},{end % 1000:03d}",
        time=f"00:00:{start // 1000:02d},{start % 1000:03d} --> 00:00:{end // 1000:02d},{end % 1000:03d}",
        line=line,
    )


class TestBaseRecognPostInit:
    def test_cjk_language_join_word_flag(self):
        rec = BaseRecogn(detect_language="zh-cn")
        assert rec.join_word_flag == ""
        assert rec.is_cjk is True
        assert rec.maxlen > 0

    def test_japanese_sets_cjk(self):
        rec = BaseRecogn(detect_language="ja")
        assert rec.is_cjk is True

    def test_english_not_cjk(self):
        rec = BaseRecogn(detect_language="en")
        assert rec.is_cjk is False
        assert rec.join_word_flag == " "

    def test_device_from_cuda(self):
        rec1 = BaseRecogn(is_cuda=True)
        assert rec1.device == "cuda"
        rec2 = BaseRecogn(is_cuda=False)
        assert rec2.device == "cpu"

    def test_flag_initialization(self):
        rec = BaseRecogn(detect_language="en")
        assert isinstance(rec.flag, list)
        assert len(rec.flag) > 0

    def test_defaults(self):
        rec = BaseRecogn()
        assert rec.recogn_type == 0
        assert rec.is_cuda is False
        assert rec.subtitle_type == 0
        assert rec.max_speakers == -1
        assert rec.recogn2pass is False


class TestPostFix:
    def test_removes_punctuation_only_lines(self):
        rec = BaseRecogn(detect_language="en", recogn_type=0)
        subs = [
            _make_srt("Hello", 0, 1000, 1),
            _make_srt("...", 1000, 2000, 2),
            _make_srt("World", 2000, 3000, 3),
        ]
        result = rec._post_fix(subs)
        texts = [it["text"] for it in result]
        assert "Hello" in texts
        assert "World" in texts

    def test_renumbers_lines(self):
        rec = BaseRecogn(detect_language="en", recogn_type=0)
        subs = [
            _make_srt("A", 0, 1000, 5),
            _make_srt("", 1000, 2000, 6),
            _make_srt("B", 2000, 3000, 7),
        ]
        result = rec._post_fix(subs)
        assert len(result) == 2
        assert result[0]["line"] == 1
        assert result[1]["line"] == 2

    def test_fixes_overlapping_timestamps(self):
        rec = BaseRecogn(detect_language="en", recogn_type=0)
        subs = [
            _make_srt("First", 0, 2000, 1),
            _make_srt("Second", 1500, 3000, 2),
        ]
        result = rec._post_fix(subs)
        assert result[0]["end_time"] == result[1]["start_time"]

    def test_recogn2pass_skips_merge(self):
        rec = BaseRecogn(detect_language="en", recogn_type=0)
        rec.recogn2pass = True
        subs = [_make_srt("Hello", 0, 1000, 1)]
        result = rec._post_fix(subs)
        assert len(result) == 1


class TestRunPostProcessing:
    def test_run_removes_invalid_segments(self, monkeypatch):
        rec = BaseRecogn(detect_language="en", recogn_type=0)
        subs = [_make_srt("Hello world", 0, 3000, 1), _make_srt("...", 3000, 3500, 2)]
        monkeypatch.setattr(rec, "_exec", lambda: subs)

        result = rec.run()

        assert len(result) == 1
        assert result[0].text == "Hello world"

    def test_second_pass_preserves_raw_segments(self, monkeypatch):
        rec = BaseRecogn(detect_language="en", recogn_type=0, recogn2pass=True)
        subs = [_make_srt("...", 0, 500, 1)]
        monkeypatch.setattr(rec, "_exec", lambda: subs)

        assert rec.run() is subs
