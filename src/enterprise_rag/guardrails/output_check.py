"""Check the answer's citations before it reaches the employee.

A citation to a source the model was never given is dropped from the text, and an answer
left with no valid citation becomes a refusal: an unsupported claim is worse than none.
"""

from __future__ import annotations

import re
from dataclasses import replace

from enterprise_rag.generation.generator import Generated

_MARKER = re.compile(r"\s?\[(\d+)\]")


def check_citations(generated: Generated, n_sources: int) -> Generated:
    if generated.refused:
        return generated
    valid = tuple(c for c in generated.citations if 1 <= c <= n_sources)
    text = _MARKER.sub(lambda m: m.group(0) if 1 <= int(m.group(1)) <= n_sources else "",
                       generated.answer)
    if not valid:
        return replace(generated, answer="", citations=(), refused=True, reason="no_support")
    return replace(generated, answer=text.strip(), citations=valid)
