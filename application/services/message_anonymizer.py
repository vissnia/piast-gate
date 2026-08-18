from typing import Dict, List, Optional, Tuple

from application.dtos.chat_request import ChatMessage
from domain.entities.pii_token import PIIToken
from domain.services.anonymizer_service import AnonymizerService


async def anonymize_messages(
    anonymizer: AnonymizerService, messages: List[ChatMessage]
) -> Tuple[List[dict], Dict[str, PIIToken]]:
    """
    Anonymizes the text content of chat messages under one shared numbering
    scheme, in preparation for sending to an LLM provider.

    Only plain text is scanned: for multimodal messages (content as a list
    of OpenAI-style content parts), only the "text" parts are anonymized —
    image parts pass through untouched. Tool calls / tool results
    (``tool_calls``, ``tool_call_id``, ``name``) also pass through
    untouched, since they are not scanned for PII in this version.
    """
    texts: List[str] = []
    locations: List[Tuple[int, Optional[int]]] = []

    for i, msg in enumerate(messages):
        if isinstance(msg.content, str):
            texts.append(msg.content)
            locations.append((i, None))
        elif isinstance(msg.content, list):
            for j, part in enumerate(msg.content):
                if part.get("type") == "text":
                    texts.append(part.get("text", ""))
                    locations.append((i, j))

    anonymized_texts, global_mapping = await anonymizer.anonymize_texts_async(texts)

    contents: List = [
        [dict(part) for part in msg.content] if isinstance(msg.content, list) else msg.content
        for msg in messages
    ]

    for (i, j), anon_text in zip(locations, anonymized_texts):
        if j is None:
            contents[i] = anon_text
        else:
            contents[i][j]["text"] = anon_text

    anonymized_messages = []
    for i, msg in enumerate(messages):
        message_dict = {"role": msg.role, "content": contents[i]}
        if msg.tool_calls is not None:
            message_dict["tool_calls"] = msg.tool_calls
        if msg.tool_call_id is not None:
            message_dict["tool_call_id"] = msg.tool_call_id
        if msg.name is not None:
            message_dict["name"] = msg.name
        anonymized_messages.append(message_dict)

    return anonymized_messages, global_mapping
