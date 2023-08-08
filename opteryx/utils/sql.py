import re


def remove_comments(string):  # pragma: no cover
    """
    Remove comments from the string
    """
    # first group captures quoted strings (double, single or back tick)
    # second group captures comments (//single-line or /* multi-line */)
    pattern = r"(\"[^\"]\"|\'[^\']\'|\`[^\`]\`)|(/\*[^\*/]*\*/|--[^\r\n]*$)"
    regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

    def _replacer(match):
        # if the 2nd group (capturing comments) is not None,
        # it means we have captured a non-quoted (real) comment string.
        if match.group(2) is not None:
            return ""  # so we will return empty to remove the comment
        # otherwise, we will return the 1st group
        return match.group(1)  # captured quoted-string

    return regex.sub(_replacer, string)


def clean_statement(string):  # pragma: no cover
    """
    Remove carriage returns and all whitespace to single spaces.

    Avoid removing whitespace in quoted strings.
    """
    pattern = r"(\"[^\"]\"|\'[^\']\'|\`[^\`]\`)|(\r\n\t\f\v+)"
    regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

    def _replacer(match):
        if match.group(2) is not None:
            return " "
        return match.group(1)  # captured quoted-string

    return regex.sub(_replacer, string).strip()


def split_sql_statements(sql: str) -> list:
    statements = []
    buffer = []
    in_single_quote = False
    in_double_quote = False
    in_backtick_quote = False

    for char in sql:
        if char == "'" and not in_double_quote and not in_backtick_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote and not in_backtick_quote:
            in_double_quote = not in_double_quote
        elif char == "`" and not in_single_quote and not in_double_quote:
            in_backtick_quote = not in_backtick_quote
        elif char == ";" and not in_single_quote and not in_double_quote and not in_backtick_quote:
            statements.append("".join(buffer).strip())
            buffer = []
            continue

        buffer.append(char)

    # Append any remaining text
    if buffer:
        statements.append("".join(buffer).strip())

    return statements
