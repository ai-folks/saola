import uuid
from saola.doc import Doc
from functools import partial
from saola.ui import ShellUI

class BaseConvo:
    def __init__(self, model=None, ui=None):
        self.bubbles = []
        self.checkpoints = []
        self.model = model() if isinstance(model, type) else model
        self.ui = ui or ShellUI()

    @property
    def system(self):
        return BubbleMaker("system", self)

    @property
    def user(self):
        return BubbleMaker("user", self)

    @property
    def assistant(self):    
        return BubbleMaker("assistant", self)

    def __getitem__(self, key):
        return self.bubbles[key]

    def bubble_maker(self, author, meta=None):
        return BubbleMaker(author, convo=self, meta=meta)

    @property
    def messages(self):
        convo = self.copy(ignore_meta=True)
        return [{'role': bubble.author, 'content': bubble.text} for bubble in convo.bubbles]

    def copy(self, ignore_meta=False):
        convo = BaseConvo(model=self.model)
        for bubble in self.bubbles: convo.bubble_maker(bubble.author, meta=None if ignore_meta else bubble.meta) << bubble.text
        return convo

    def _stream_to_bubble_handler(self, bubble_box, author, chunk, ending):
        bubble = bubble_box[0] or self.bubble_maker(author) << ""
        bubble_box[0] = bubble
        bubble.doc.text += chunk or ""

    def stream_answer(self, *handlers):
        bubble_box = [None]
        for (_, chunk, _) in self.model.stream_answer(self.messages, *handlers, partial(self._stream_to_bubble_handler, bubble_box)):
            yield (bubble_box[0], chunk)

    def stream_answer_to_end(self, *handlers):
        bubble = None
        for (b, _) in self.stream_answer(*handlers): bubble = b
        return bubble

    def answer(self):
        return self.model.answer(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def tag_bubble_with_uuid(self):
        if len(self.bubbles) == 0: return
        meta = self.bubbles[-1].meta or {}
        if 'checkpoint_uuid' in meta: return
        self.bubbles[-1].meta = dict(**meta, checkpoint_uuid=str(uuid.uuid4()))

    def checkpoint(self):
        self.tag_bubble_with_uuid()
        self.checkpoints.append(len(self.bubbles))
        return self.checkpoints[-1]

    def rollback(self, checkpoint=None):
        checkpoint = checkpoint or (self.checkpoints[-1] if len(self.checkpoints) > 0 else 0)
        self.checkpoints = [c for c in self.checkpoints if c < checkpoint]
        self.bubbles = self.bubbles[:checkpoint]

    def loop(self):
        with self:
            while True:
                self.ui.display_user_header()
                self.user << self.ui.get_user_input()
                self.ui.display_assistant_header()
                self.stream_answer_to_end(self.ui.append_to_assistant_output)
            

class Bubble:
    def __init__(self, author, convo, meta=None):
        self.author = author
        self.convo = convo
        self.meta = meta
        self.doc = Doc()
        self.convo.bubbles.append(self)

    def __lshift__(self, text):
        self.doc.append_with_newline(str(text))
        return self

    @property
    def text(self):
        return self.doc.text

class BubbleMaker:
    def __init__(self, author, convo, meta=None):
        self.author = author
        self.convo = convo
        self.meta = meta

    def __call__(self, **kwargs):
        self.meta = kwargs
        return self

    def _matches_convo_last_bubble(self):
        return len(self.convo.bubbles) > 0 and self.convo.bubbles[-1].author == self.author and self.convo.bubbles[-1].meta == self.meta

    def __lshift__(self, text):
        if self._matches_convo_last_bubble():
            return self.convo.bubbles[-1] << text
        else:
            return Bubble(self.author, self.convo, meta=self.meta) << text