from application.services.thinking_parser import ThinkingParser


def _content(chunks):
    return "".join(c for c, _ in chunks)


def _thinking(chunks):
    return "".join(t for _, t in chunks)


class TestThinkingParser:
    def test_plain_text_without_thinking_block(self):
        parser = ThinkingParser()
        chunks = parser.process("Hello world")

        assert chunks == [("Hello world", "")]

    def test_full_thinking_block_in_a_single_call(self):
        parser = ThinkingParser()
        chunks = parser.process("before<think>reasoning</think>after")

        assert _content(chunks) == "beforeafter"
        assert _thinking(chunks) == "reasoning"

    def test_thinking_block_spanning_multiple_process_calls(self):
        """
        The state machine must carry `in_thinking_block` across calls, since
        a real stream delivers the model's reasoning one small delta at a
        time rather than as a single string.
        """
        parser = ThinkingParser()
        results = []
        results += parser.process("before <think>")
        results += parser.process("step one. ")
        results += parser.process("step two.</think> after")

        assert _content(results) == "before  after"
        assert _thinking(results) == "step one. step two."

    def test_multiple_thinking_blocks(self):
        parser = ThinkingParser()
        chunks = parser.process("<think>a</think>mid<think>b</think>end")

        assert _content(chunks) == "midend"
        assert _thinking(chunks) == "ab"

    def test_open_tag_split_across_process_calls_is_not_reassembled(self):
        """
        Pins down a real limitation: unlike StreamDeanonymizer (which buffers
        a `<...>` span char-by-char so a tag can never arrive split), this
        parser only recognises `<think>`/`</think>` when they're intact
        within a single `process()` call. If the tag itself straddles a
        chunk boundary, the fragments leak through as ordinary content
        instead of opening a thinking block.

        Today this never happens in practice: in the real streaming
        pipeline (StreamChatUseCase), ThinkingParser only ever sees text
        that has already passed through StreamDeanonymizer, which
        guarantees any `<...>`-shaped span is delivered whole. This test
        exists to make that dependency explicit — if it ever starts
        failing because someone "fixed" ThinkingParser to reassemble split
        tags, that's fine; but if the pipeline ordering changes such that
        ThinkingParser receives raw, unreassembled provider output, this
        gap becomes a live bug.
        """
        parser = ThinkingParser()
        results = []
        results += parser.process("before <thi")
        results += parser.process("nk>reasoning</think> after")

        assert _content(results) == "before <think>reasoning</think> after"
        assert _thinking(results) == ""

    def test_empty_string_returns_no_chunks(self):
        parser = ThinkingParser()
        assert parser.process("") == []
