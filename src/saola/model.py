import os
from openai import OpenAI
from collections import namedtuple

# STREAM HANDLERS
# ===============
# Stream handlers are functions that take:
# - author: The author of the new chunk of text (sometimes shows up only on the first chunk).
# - chunk: The new chunk of text (possibly None).
# - ending: True if this is the last message in the stream (in this case, chunk will be None).
# And they return a triplet containing:
# - Either True (meaning keep the chunk as is) or a new chunk of text that replaces the current chunk.
# - True if the chunk should be yielded to the next handler (and the caller).
# - True if the stream should continue after yielding (or not yielding) to the caller.

# A namedtuple for stream handler results
R = namedtuple("StreamHandlerResult", ["chunk", "should_yield", "should_continue"])

def _convert_chunk(original_chunk, new_chunk):
    if new_chunk is True: return original_chunk
    return new_chunk or ""

# Stream handlers are composable
def _compose_stream_handlers(*handlers):
    def handler(*, author, chunk, ending):
        should_yield = True
        should_continue = True
        for h in handlers:
            if not h: continue
            if not should_yield: break
            handler_result = h(author=author, chunk=chunk, ending=ending) \
                or R(chunk=True, should_yield=True, should_continue=True)
            chunk = _convert_chunk(chunk, handler_result.chunk)
            should_yield = should_yield and handler_result.should_yield
            should_continue = should_continue and handler_result.should_continue
        return R(chunk=chunk, should_yield=should_yield, should_continue=should_continue)
    return handler

class Model:
    def _stream_answer_nonstop(self, messages):
        raise NotImplementedError()
    
    def _get_answer(self, messages):
        raise NotImplementedError()

    def stream_answer(self, messages, *handlers):
        handler = _compose_stream_handlers(*handlers)
        broken = False
        for (author, chunk) in self._stream_answer_nonstop(messages):
            handler_result = handler(author=author, chunk=chunk, ending=False)
            if handler_result.should_yield: yield (author, chunk, False)
            if not handler_result.should_continue:
                broken = True
                break
        if not broken:
            handler_result = handler(author=None, chunk=None, ending=True)
            if handler_result.should_yield: yield (None, None, True)

    def get_answer(self, messages):
        return self._get_answer(messages)

class OpenAIModel(Model):
    def __init__(self, model_name, organization=None, api_key=None):
        self.model_name = model_name
        organization = organization or os.getenv("OPENAI_ORGANIZATION")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(organization=organization, api_key=api_key)

    def _stream_answer_nonstop(self, messages):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True
        )
        for chunk in response:
            author = chunk.choices[0].delta.role or "assistant"
            text_chunk = chunk.choices[0].delta.content or None
            yield (author, text_chunk)

    def _get_answer(self, messages):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False
        )
        author = response.choices[0].message.role or "assistant"
        text = response.choices[0].message.content
        return (author, text)
        
class OpenAIGPT35Turbo(OpenAIModel):
    def __init__(self, api_key=None):
        super().__init__("gpt-3.5-turbo", api_key=api_key)

class OpenAIGPT4(OpenAIModel):
    def __init__(self, api_key=None):
        super().__init__("gpt-4", api_key=api_key)

class OpenAIGPT4TurboPreview(OpenAIModel):
    def __init__(self, api_key=None):
        super().__init__("gpt-4-1106-preview", api_key=api_key)

