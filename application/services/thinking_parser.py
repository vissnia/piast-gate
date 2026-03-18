class ThinkingParser:
    def __init__(self) -> None:
        self.in_thinking_block = False

    def process(self, text: str) -> list[tuple[str, str]]:
        """
        Returns list of (content, thinking)
        """
        result = []
        current = text

        while current:
            if not self.in_thinking_block:
                if "<think>" in current:
                    before, after = current.split("<think>", 1)
                    if before:
                        result.append((before, ""))
                    self.in_thinking_block = True
                    current = after
                else:
                    result.append((current, ""))
                    break
            else:
                if "</think>" in current:
                    before, after = current.split("</think>", 1)
                    if before:
                        result.append(("", before))
                    self.in_thinking_block = False
                    current = after
                else:
                    result.append(("", current))
                    break

        return result