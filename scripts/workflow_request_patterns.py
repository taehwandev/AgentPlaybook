"""Regex patterns used by workflow request classification."""

from __future__ import annotations


DIRECT_QUESTION_PATTERNS = (
    r"\?",
    r"\b(what|when|where|why|how|which|who|should|do i|does|is|are|can i)\b",
    "\uc5b8\uc81c",
    "\ubb34\uc5c7",
    "\ubb50",
    "\uc5b4\ub5bb\uac8c",
    "\uc65c",
    "\uc5b4\ub514",
    "\uc5b4\ub290",
    "\ub204\uac00",
    "\uc778\uac00",
    "\ub9de\uc544",
    "\uac70\uc57c",
    "\uac74\uac00",
    "\ub098\uc694",
    "\ud569\ub2c8\uae4c",
    "\ud560\uae4c",
)
QUESTION_ACTION_PATTERNS = (
    r"\b(can you|could you|would you|please|go ahead and)\b",
    "\ud574\uc918",
    "\ud574\uc8fc\uc138\uc694",
    "\ud574\uc904\ub798",
    "\ubc14\uafd4\uc918",
    "\uace0\uccd0\uc918",
    "\uc218\uc815\ud574\uc918",
    "\uc801\uc6a9\ud574\uc918",
    "\ucd94\uac00\ud574\uc918",
    "\uba85\uc2dc\ud574\uc918",
    "\ub123\uc5b4\uc918",
    "\ub2f4\uc544\uc918",
    "\uc791\uc131\ud558\uc790",
    r"\uc791\uc131\s*\ub2e4\uc2dc\s*\ud558\uc790",
    r"\ub2e4\uc2dc\s*(\uc791\uc131|\uc4f0|\uc815\ub9ac)\ud558\uc790",
    "\uc815\ub9ac\ud558\uc790",
    "\uc801\uc6a9",
    "\ub2e4\uc2dc \uc801\uc6a9",
    "\ucee4\ubc0b\ud574\uc918",
    "\ud478\uc26c\ud574\uc918",
    "\uc2e4\ud589\ud574\uc918",
    "\ub9cc\ub4e4\uc5b4\uc918",
    r"(\ud574\ubcf4\uc790|\uc9c4\ud589\ud574\uc918|\ud30c\uc545\ud574\uc918|\ud30c\uc545\uc880)",
)
EXACT_PATTERNS = (
    r"`[^`]+`",
    r"(?:^|\s)(?:~/|\.{1,2}/|/)[A-Za-z0-9_./-]+",
    r"\b[\w./-]+\.(kt|swift|tsx|ts|jsx|js|py|go|rs|java|md|json|yml|yaml|toml)\b",
    r":\d+\b",
    r"\b(error|exception|traceback|stack trace|compiler|lint|test failed|failing test)\b",
    r"\b(nullpointer|typeerror|referenceerror|syntaxerror|segmentation fault)\b",
)
SCOPED_PATTERNS = (
    r"\b[A-Z][A-Za-z0-9]*(Screen|View|ViewModel|Controller|Route|Page|Component|Service|Repository|UseCase)",
    r"\b(home|settings|profile|checkout|billing|invite|member|login|signup)\b.*\b(button|form|screen|page|modal|dialog|tab)\b",
)
BROAD_PATTERNS = (
    r"\b(build|implement|design|create|add|plan)\b.*\b(feature|flow|system|architecture|prd|ard|product)\b",
    r"\b(auth|rbac|permission|billing|entitlement|invite|tenant|migration|release|deployment)\b",
    r"(\uc571|\uae30\ub2a5|\ud654\uba74|\uc81c\ud488|\ud50c\ub85c\uc6b0|\uc11c\ube44\uc2a4).*(\ub9cc\ub4e4|\ub9cc\ub4dc|\uad6c\ud604|\uc124\uacc4|\ucd94\uac00|\uc791\uc5c5|\uc9c4\ud589)|prd|ard|\uc694\uad6c\uc0ac\ud56d|\uc544\ud0a4\ud14d\ucc98",
)
RISKY_PATTERNS = (
    r"\b(delete|drop|destroy|migrate|deploy|release|publish|payment|billing|secret|token|credential|permission|security|tenant)\b",
)
VAGUE_PATTERNS = (
    r"\b(fix|improve|clean up|make better|change|update|adjust|modify)\b",
    r"\b(rewrite|rework|revise|redraft|rephrase|polish|tighten)\b",
    r"\b(button|home|screen|ui|layout|style)\b",
    r"\ub2e4\uc2dc\s*(\uc791\uc131|\uc4f0|\uc815\ub9ac)",
    r"\uc791\uc131\s*\ub2e4\uc2dc",
    "\uc7ac\uc791\uc131",
    "\ubb38\uccb4",
    "\ub9d0\ud22c",
    "\uc5b4\ud22c",
    "\uc2a4\ud0c0\uc77c",
    "\ub0b4 \uc2a4\ud0c0\uc77c",
    "\uc874\ub300",
)
GRILL_ME_REQUEST_PATTERNS = (
    r"\bgrill me\b",
    r"\b(run|use|invoke|start|do)\s+(the\s+)?grill[- ]?me\b",
    r"\bgrill[- ]?me\s+(this|me|my|us|please)\b",
    r"\bask me questions\b",
    r"\bhelp define requirements\b",
    r"\bquestion drill\b",
    r"\uadf8\ub9b4\ubbf8\s*(\ud574\uc918|\ud574\uc8fc\uc138\uc694|\ud574|\ud558\uc790|\ub3cc\ub824|\uc2e4\ud589|\uc368|\uc9c8\ubb38)",
)

DRILL_PHRASES = GRILL_ME_REQUEST_PATTERNS
