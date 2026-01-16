import tiktoken
def count_tokens(text, encoding):
 tokens = tiktoken.tokenize(text, encoding)
 return len(tokens)