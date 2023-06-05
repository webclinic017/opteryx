import re


def tokenize_string(string):
    # Define the regular expression to match tokens
    token_pattern = re.compile(r"[(),]|[^\s(),]+")

    # Use the regular expression to find all tokens in the string
    tokens = token_pattern.findall(string)

    # Remove any leading or trailing whitespace from the tokens
    tokens = [token.strip() for token in tokens]

    return tokens


def format_sql(sql):
    words = tokenize_string(sql)

    formatted_sql = ""
    in_string_literal = False

    for i, word in enumerate(words):
        if word in ("(", ")"):
            formatted_sql += "\033[38;2;98;114;164m" + word + "\033[0m "
        elif not in_string_literal and word.startswith("'"):
            formatted_sql += "\033[38;5;203m" + word
            if word.endswith("'"):
                in_string_literal = False
                formatted_sql += "\033[0m "
        elif in_string_literal:
            formatted_sql += word + " "
            if word.endswith("'"):
                in_string_literal = False
                formatted_sql += "\033[0m"
        elif (i + 1) < len(words) and words[i + 1] == "(":
            formatted_sql += "\033[38;2;80;250;123m" + word.upper() + "\033[0m"
        elif word in (
            "SELECT",
            "FROM",
            "WHERE",
            "JOIN",
            "ON",
            "AND",
            "OR",
            "GROUP",
            "BY",
            "ORDER",
            "LIMIT",
            "LIKE",
            "ILIKE",
            "UNION",
            "LEFT",
            "RIGHT",
            "FULL",
            "OUTER",
            "INNER",
        ):
            formatted_sql += "\033[38;2;139;233;253m" + word + "\033[0m "
        elif word in ("=", ">=", "<=", "!=", "<", ">", "<>"):
            formatted_sql += "\033[38;5;183m" + word + "\033[0m "
        elif word.isdigit():
            formatted_sql += "\033[38;2;255;184;108m" + word + "\033[0m "
        else:
            formatted_sql += word + " "

    formatted_sql += "\033[0m"

    formatted_sql = formatted_sql.replace(" \033[38;2;98;114;164m(", "\033[38;2;98;114;164m(")
    formatted_sql = formatted_sql.replace("(\033[0m ", "(\033[0m")
    formatted_sql = formatted_sql.replace(" \033[38;2;98;114;164m)", "\033[38;2;98;114;164m)")
    formatted_sql = formatted_sql.replace(" ,", ",")

    return "\n" + formatted_sql.strip()
