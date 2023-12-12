import os
import subprocess
from saola.base_convo import BaseConvo
from saola.model import R


class Convo(BaseConvo):
    def __init__(self, model, *, ui=None, interfaces=None, safety_checks=True):
        super().__init__(model, ui=ui)
        self.current_streaming_bubble = None
        self.current_matching_interface = None
        self.interfaces = interfaces or []
        self.safety_checks = safety_checks
        if len(self.interfaces) > 0:
            self.system << """
            You are a useful AI assistant that has just been equiped with the novel ability to to leverage a collection of "interfaces" to access real-time data and external systems, directly in-chat, in order to answer the user's questions or fulfill user requests. You try to answer all the user's questions and perform the tasks requested by the user, and you promptly leverage the available interfaces whenever needed. These interfaces allow you to perform tasks that a normal LLM-based assistant would not be able to perform.
            To trigger an interface, you start in a new line with [__INTERFACE_NAME__], followed by your command, ending with [/__INTERFACE_NAME__], followed by a line break. The output of this command will show up in the chat and you may proceed to answer questions and requests based on those outputs.
            The available interfaces are listed below.
            """
            for interface in self.interfaces:
                self.system << f"""
                {interface.name} Interface:
                [__{interface.name}__]...[/__{interface.name}__]
                """
                self.system << interface.explanation
            # TODO: Consider removing this and restoring it depending on whether new version of GPT will require this instruction.
            # self.system << f"""
            # Feel free to go step by step when following instructions from the user. It is ok to ask for clarification questions, or to use the interfaces provided to find out more information before performing an action.
            # """
    
    def stream_answer(self, *handlers):
        self.current_streaming_bubble = None
        while True:
            for (bubble, chunk) in super().stream_answer(*[i(self) for i in self.interfaces], *handlers):
                self.current_streaming_bubble = bubble
                yield (bubble, chunk)
            output = self.current_matching_interface._execute() if self.current_matching_interface else None
            if output:
                self.ui.display_interface_output(output)
                self.current_streaming_bubble.doc.append_with_newline("-- OUTPUT --\n" + output + "\n-- END OUTPUT --")
            else:
                break
        self.current_streaming_bubble = None

     # Method for updating context
    def update_context(self, new_context):
        """
        Updates the system's conversation context with new information.
        
        :param new_context: A string that contains the new context to be added.
        """
        self.system << new_context

class Interface:
    safety_checks = True

    def __init__(self, convo):
        self.convo = convo
        self.pattern_start_pos = -1
        self.pattern_end_pos = -1
        self.current_code = None

    @property
    def pattern_start(self):
        return f"[__{self.name}__]"
    
    @property
    def pattern_end(self):
        return f"[/__{self.name}__]" + os.linesep

    def execute(self, code):
        raise NotImplementedError()

    def _execute(self):
        self.convo.current_matching_interface = None
        if self.current_code is None: return None
        if ((not self.safety_checks or not self.convo.safety_checks) and self.convo.ui.no_safety_confirmation()) \
           or self.convo.ui.safety_confirmation(f"[red1] Execute {self.name} code? [/red1]"):
            output = self.execute(self.current_code) or "<empty output>"
        else:
            output = f"The user prevented this {self.name} code from running. This was a manual action and not an error of the code itself. The user may have an explanation for their decision."
        return output
    
    def _find_substring(self, substring, text, chunk, needs_newline):
        # Finds substring in text + chunk, if it intersects with chunk
        assert len(substring) >= 1, "Interface substrings (pattern starts and ends) must not be empty!"
        extended_chunk = (text[-len(substring) + 1:] if len(substring) > 1 else "") + chunk
        pos = extended_chunk.find(substring)
        if pos == -1: return -1
        full_text = text + chunk
        pos += len(full_text) - len(extended_chunk)
        text_until_substring = full_text[:pos]
        if needs_newline and text_until_substring and not text_until_substring.endswith(os.linesep): return -1
        return pos
    
    def _find_pattern_start(self, text, chunk):
        return self._find_substring(self.pattern_start, text, chunk, needs_newline=True)
    
    def _find_pattern_end(self, text, chunk):
        return self._find_substring(self.pattern_end, text, chunk, needs_newline=False)
    
    def __call__(self, author, chunk, ending):
        if self.convo.current_matching_interface and self.convo.current_matching_interface is not self: return None
        if not ending and not chunk: return None
        if ending: chunk = os.linesep
        text = self.convo.current_streaming_bubble.text if self.convo.current_streaming_bubble else ""
        if self.pattern_start_pos == -1:
            self.pattern_start_pos = self._find_pattern_start(text, chunk)
            if self.pattern_start_pos == -1: return None
        self.convo.current_matching_interface = self
        if self.pattern_end_pos == -1:
            self.pattern_end_pos = self._find_pattern_end(text, chunk)
            if self.pattern_end_pos < self.pattern_start_pos + len(self.pattern_start):
                self.pattern_end_pos = -1
                return None
        assert self.pattern_start_pos < self.pattern_end_pos, "Prompt start position must be before prompt end position!"
        full_text = text + chunk
        self.current_code = full_text[self.pattern_start_pos + len(self.pattern_start):self.pattern_end_pos]
        new_text = full_text[:self.pattern_end_pos + len(self.pattern_end)]
        new_chunk = new_text[len(text):].rstrip(os.linesep)
        return R(chunk=new_chunk, should_yield=True, should_continue=False)

class ShellInterface(Interface):
    name = "SHELL"
    explanation = f"""
    This interface allows you to run commands on the user's shell console. For example you may execute the command "date" to retrieve the current time, or ping a website to check for internet connectivity. The output of your command will show up in the chat and you may proceed to answer questions and requests based on those outputs. Tip: When you execute a command, the user may see the output, so you can make reference to it, but there is no need to repeat it in your answer. For example, if you execute a cat statement, there is no need to repeat the contents of the file in your answer after that.
    An important thing to know is that each shell command is independent, so instead of running for example "cd some_path" followed by "ls", you will probably need to do "ls some_path" or "cd some_path && ls" instead.
    In case this is useful, here is some information about the user's system: {os.uname()}. Also the user's username is {os.getlogin()}.
    """
    max_output_length = None

    def execute(self, code):
        process = subprocess.Popen(code.strip(), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")
        if self.max_output_length and len(stdout) > self.max_output_length: stdout = stdout[:self.max_output_length].rstrip("\n") + "\n-- STDOUT TRIMMED FOR BEING TOO LONG --"
        if self.max_output_length and len(stderr) > self.max_output_length: stderr = stderr[:self.max_output_length].rstrip("\n") + "\n-- STDERR TRIMMED FOR BEING TOO LONG --"
        output = (stdout + stderr).rstrip('\n')
        return output
    
class FileWriteInterface(Interface):
    name = "FILE_WRITE"
    explanation = """
    This interface allows you to write a new file or replace the contents of a file in the user's filesystem. The first line of your command is the path to the file to be created or replaced. The new contents of the file should start on the next line. This will cause the file to be written to the filesystem of the user. Remember to always write the intended file content entirely. Avoid stubbing like "keep this part as is" as that would be written verbatim to the file.
    """

    def execute(self, code):
        try:
            args = code.lstrip().split(os.linesep, 1)
            if len(args) == 1: args = args + [""]
            first_line, contents = args
            file_path = first_line.strip()
            file_path = os.path.abspath(os.path.expanduser(file_path))
            base_folder = os.path.dirname(file_path)
            if base_folder and not os.path.exists(base_folder): os.makedirs(base_folder)
            with open(file_path, "w") as f: f.write(contents)
            return f"File written to {file_path}"
        except Exception as e:
            return f"ERROR: {e}"