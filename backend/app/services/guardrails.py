import re
import logging

logger = logging.getLogger(__name__)

MAX_QUERY_LEN = 700


# Direct instruction overrides
_OVERRIDE_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|context)",
    r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    r"override\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    r"do\s+not\s+follow\s+(the\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?)",
]

# Role hijacking — trying to redefine the system persona
_ROLE_HIJACK_PATTERNS = [
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(a\s+|an\s+)?(?!financial|finance)",  # "act as" is ok only for finance
    r"pretend\s+(you\s+are|to\s+be)\s+",
    r"your\s+new\s+(role|persona|identity|instructions?)\s+(is|are)",
    r"switch\s+to\s+.{0,20}(mode|persona|role)",
    r"from\s+now\s+on\s+you\s+(are|will|should|must)",
]

# System prompt extraction
_EXTRACTION_PATTERNS = [
    r"(show|reveal|print|output|display|repeat|echo)\s+(me\s+)?(your|the|system)\s+(system\s+)?(prompt|instructions?|rules?|persona)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?)",
    r"(give|tell)\s+me\s+your\s+(system\s+)?(prompt|instructions?|rules?)",
]

# Delimiter / context escape attempts
_ESCAPE_PATTERNS = [
    r"<\s*/?\s*system\s*>",
    r"\[/?system\]",
    r"```\s*(system|prompt|instructions?)",
    r"---\s*(new|system|override)\s*(prompt|instructions?|context)?",
    r"={3,}\s*(system|new)\s*(prompt|instructions?)?",
    r"END\s+OF\s+(SYSTEM|CONTEXT|INSTRUCTIONS?)",
    r"BEGIN\s+NEW\s+(INSTRUCTIONS?|PROMPT|CONTEXT)",
]

# Dangerous output format manipulation
_FORMAT_MANIPULATION = [
    r"(respond|reply|answer)\s+(only\s+)?(in|with)\s+(json|xml|html|code|python|javascript)",
    r"(output|return|generate)\s+.{0,20}(code|script|executable)",
]


def _compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    return [
        re.compile(p, re.IGNORECASE | re.DOTALL)
        for p in patterns
    ]


_COMPILED = {
    "instruction_override": _compile_patterns(_OVERRIDE_PATTERNS),
    "role_hijacking": _compile_patterns(_ROLE_HIJACK_PATTERNS),
    "prompt_extraction": _compile_patterns(_EXTRACTION_PATTERNS),
    "context_escape": _compile_patterns(_ESCAPE_PATTERNS),
    "format_manipulation": _compile_patterns(_FORMAT_MANIPULATION),
}

_USER_MESSAGES = {
    "instruction_override": (
        "Your query appears to contain instructions that conflict "
        "with the system's guidelines. Please rephrase your "
        "financial question."
    ),
    "role_hijacking": (
        "FinLens can only answer questions about your uploaded "
        "financial documents. Please ask a relevant question."
    ),
    "prompt_extraction": (
        "System configuration details cannot be shared. "
        "Please ask a question about your documents."
    ),
    "context_escape": (
        "Your query contains formatting that is not supported. "
        "Please rephrase your question in plain text."
    ),
    "format_manipulation": (
        "FinLens responds in natural language only. "
        "Please ask a financial question about your documents."
    ),
}


def check_prompt_injection(query: str) -> str | None:
    text = query.strip()

    for category, patterns in _COMPILED.items():
        for pattern in patterns:
            if pattern.search(text):
                logger.warning(
                    "Prompt injection blocked [%s]: %.80s...",
                    category,
                    text,
                )
                return _USER_MESSAGES[category]

    return None


def validate_query(query: str) -> str | None:
    query = query.strip()

    if not query:
        return "Send a Query."

    if len(query) > MAX_QUERY_LEN:
        return (
            f"Query is too long. "
            f"Maximum length is {MAX_QUERY_LEN} characters."
        )

    injection_error = check_prompt_injection(query)
    if injection_error:
        return injection_error

    return None


# ── Indirect injection: malicious content hidden in documents ─────

# Extra patterns for document-embedded attacks (broader than query patterns)
_DOC_INJECTION_PATTERNS = _compile_patterns([
    # Everything from the query-level patterns
    *_OVERRIDE_PATTERNS,
    *_ROLE_HIJACK_PATTERNS,
    *_EXTRACTION_PATTERNS,
    *_ESCAPE_PATTERNS,
    *_FORMAT_MANIPULATION,

    # Doc-specific: hidden instructions targeting the LLM
    r"(AI|assistant|model|system|chatbot|FinLens)[,:]?\s+(please\s+)?(ignore|disregard|forget|override)",
    r"(when\s+asked|if\s+someone\s+asks|upon\s+receiving)",
    r"(do\s+not\s+mention|never\s+mention|hide)\s+this\s+(text|paragraph|section|instruction)",
    r"(insert|inject|embed)\s+(this\s+)?(into|in)\s+(your|the)\s+(response|answer|output)",
])


def sanitize_chunks(chunks: list[dict]) -> list[dict]:
    sanitized = []

    for chunk in chunks:
        content = chunk["content"]
        flagged = False

        for pattern in _DOC_INJECTION_PATTERNS:
            if pattern.search(content):
                flagged = True
                content = pattern.sub("[CONTENT REDACTED]", content)

        if flagged:
            logger.warning(
                "Indirect injection redacted in chunk %s (doc: %s, page: %s)",
                chunk.get("id", "?"),
                chunk.get("document_filename", "?"),
                chunk.get("page_number", "?"),
            )

        clean_chunk = chunk.copy()
        clean_chunk["content"] = content
        sanitized.append(clean_chunk)

    return sanitized
