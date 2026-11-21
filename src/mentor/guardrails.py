"""Fail-closed input and output checks for practice-mode hints."""

import ast
import re

_INJECTION = re.compile(
    r"\b(ignore|disregard|override|bypass|forget)\b.{0,60}\b(previous|above|system|developer|all|instructions?|rules?)\b"
    r"|\b(system prompt|developer message|reveal (the )?prompt|jailbreak)\b"
    r"|\b(you are now|act as|pretend to be)\b.{0,50}\b(system|developer|unrestricted|unfiltered)\b",
    re.IGNORECASE | re.DOTALL,
)
_SOLUTION_REQUEST = re.compile(
    r"\b(write|give|show|provide|dump|generate|print)\b.{0,50}\b(code|solution|implementation|answer)\b"
    r"|\b(full|complete|entire)\s+(working\s+)?(code|solution|answer)\b"
    r"|\b(solve|answer)\s+(this|it|the problem)\s+for me\b",
    re.IGNORECASE | re.DOTALL,
)
_CODE_SHAPE = re.compile(
    r"```|^\s*(def |class |import |from \w+ import |return\b|for\s+\w+\s+in\s|while\s+.+:|#include\b)|"
    r"\b(?:print|console\.log)\s*\(|\bfunction\s+\w+\s*\(|\b(?:const|let|var)\s+\w+|=>|\bstd::|\w+\s*:=\s*|;\s*$",
    re.IGNORECASE | re.MULTILINE,
)


class GuardrailError(ValueError):
    """Request or output violates the practice-mode safety boundary."""


def validate_mentor_request(question: str) -> None:
    normalized = " ".join(question.split())
    if not normalized:
        raise GuardrailError("Ask a question about the selected LeetCode problem.")
    if _INJECTION.search(normalized):
        raise GuardrailError(
            "Prompt override requests are not allowed in practice mode."
        )
    if _SOLUTION_REQUEST.search(normalized):
        raise GuardrailError(
            "Full code and solution requests are blocked; ask for a hint instead."
        )


def contains_executable_solution(text: str) -> bool:
    """Conservative regex plus Python AST detection for executable answer-shaped output."""
    if _CODE_SHAPE.search(text):
        return True
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    executable = (
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.Import,
        ast.ImportFrom,
        ast.Assign,
        ast.AnnAssign,
        ast.AugAssign,
        ast.Return,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.If,
        ast.With,
        ast.Try,
        ast.Lambda,
        ast.Call,
        ast.ListComp,
        ast.GeneratorExp,
        ast.DictComp,
        ast.SetComp,
    )
    return any(isinstance(node, executable) for node in ast.walk(tree))


def enforce_safe_output(text: str) -> str:
    if len(text.split()) > 70:
        raise GuardrailError("Mentor output exceeded the hint-length limit.")
    if contains_executable_solution(text):
        raise GuardrailError(
            "Unsafe executable content was blocked from mentor output."
        )
    return text
