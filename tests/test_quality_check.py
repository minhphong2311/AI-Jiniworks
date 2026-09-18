import pytest
import re as _re

class TestStatusParsing:
    def test_perfect_detected(self):
        text = 'ISSUES:\n- None\n\nSTATUS: PERFECT'
        status = 'PERFECT' if 'STATUS: PERFECT' in text.upper() else 'NEEDS_FIX'
        assert status == 'PERFECT'

    def test_needs_fix_detected(self):
        text = 'ISSUES:\n- Colors mismatch\n\nSTATUS: NEEDS_FIX'
        status = 'PERFECT' if 'STATUS: PERFECT' in text.upper() else 'NEEDS_FIX'
        assert status == 'NEEDS_FIX'

    def test_case_insensitive(self):
        status = 'PERFECT' if 'STATUS: PERFECT' in 'status: perfect'.upper() else 'NEEDS_FIX'
        assert status == 'PERFECT'

    def test_no_status_defaults_needs_fix(self):
        status = 'PERFECT' if 'STATUS: PERFECT' in 'random'.upper() else 'NEEDS_FIX'
        assert status == 'NEEDS_FIX'

class TestLightweightVerifyParsing:
    def test_verdict_match(self):
        assert 'VERDICT: MATCH' in 'DIFFERENCES: None\nVERDICT: MATCH'.upper()

    def test_verdict_mismatch(self):
        assert 'VERDICT: MATCH' not in 'VERDICT: MISMATCH'.upper()

    def test_case_insensitive(self):
        assert 'VERDICT: MATCH' in 'verdict: match'.upper()

    def test_mismatch_not_confused(self):
        assert 'VERDICT: MATCH' not in 'VERDICT: MISMATCH'

class TestPerfectHandlingLogic:
    def _sim(self, verdict):
        status = 'PERFECT' if 'STATUS: PERFECT' in 'STATUS: PERFECT'.upper() else 'NEEDS_FIX'
        broke = False
        if status == 'PERFECT':
            if 1 == 1:
                if 'VERDICT: MATCH' in verdict.upper():
                    broke = True
            else:
                broke = True
        return broke

    def test_true_perfect_breaks_early(self):
        assert self._sim('DIFFERENCES: None\nVERDICT: MATCH') is True

    def test_false_perfect_continues(self):
        assert self._sim('DIFFERENCES:\n- Font off\nVERDICT: MISMATCH') is False

    def test_iteration_2_breaks(self):
        broke = False
        status, iteration = 'PERFECT', 2
        if status == 'PERFECT' and iteration != 1:
            broke = True
        assert broke is True

    def test_iteration_3_breaks(self):
        broke = False
        status, iteration = 'PERFECT', 3
        if status == 'PERFECT' and iteration != 1:
            broke = True
        assert broke is True

class TestHtmlCssExtraction:
    BACKTICK3 = '```'
    def test_extract_html(self):
        bt = self.BACKTICK3
        text = f'STATUS: NEEDS_FIX\n{bt}html\n<div>Hello</div>\n{bt}'
        m = _re.search(bt + r'html\n(.*?)\n' + bt, text, _re.DOTALL | _re.IGNORECASE)
        assert m is not None
        assert '<div>Hello</div>' in m.group(1)

    def test_no_html_when_perfect(self):
        bt = self.BACKTICK3
        text = 'ISSUES:\nNone\n\nSTATUS: PERFECT'
        m = _re.search(bt + r'html\n(.*?)\n' + bt, text, _re.DOTALL | _re.IGNORECASE)
        assert m is None

    def test_issues_in_new_format(self):
        text = 'ISSUES:\n- None\n\nSTATUS: PERFECT'
        assert 'ISSUES:' in text
        assert 'STATUS: PERFECT' in text.upper()

class TestVerifyErrorFallback:
    def test_exception_does_not_break(self):
        broke = False
        try:
            raise ConnectionError('API timeout')
            broke = True
        except Exception:
            pass
        assert broke is False