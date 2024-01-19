EXPLAIN = """
Explain in MAXIMUM {num_tokens} TOKENS what the following code does: 
{code}
""".strip()

EXPLAIN_MODULE = """
Explain in around {num_tokens} tokens what the following module does. 
DO NOT include the name of functions or classes in your explanation, only what is does.
Be as concised as you can, trying to capture all of the functionalities in as few words as you can.
CODE:
{code}
""".strip()

SUMMARIZE_MODULE = """
Summarize the following text related to a module in MAXIMUM {num_tokens} TOKENS.
Be as concised as you can, trying to capture all of the functionalities in as few words as you can.
{text}
""".strip()