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
            interface = self.current_matching_interface
            meta = interface.meta if interface else None
            output = interface._execute() if interface else None
            if output:
                self.ui.display_interface_output(output)
                self.bubble_maker(self.current_streaming_bubble.author, meta=meta or self.current_streaming_bubble.meta) << \
                    "-- OUTPUT --\n" + output + "\n-- END OUTPUT --"
                interface.cleanup()
            else:
                break
        self.current_streaming_bubble = None

class Interface:
    safety_checks = True
    empty_output = "<empty output>"

    def __init__(self, convo):
        self.convo = convo
        self.pattern_start_pos = -1
        self.pattern_end_pos = -1
        self.current_code = None
        self.meta = {'interface': self.name}

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
            output = self.execute(self.current_code) or self.empty_output
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
    
    def cleanup(self):
        pass

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
    
class PythonInterface(Interface):
    name = "PYTHON"
    explanation = """
    This interface allows you to run Python code. The input of your command is the Python code to be executed, in an isolated scope. The output of your command is the result of the Python code. You may use this interface to perform calculations, manipulate data, or run any Python code that you need. The stdout (e.g. outputs of print calls) and stderr of your code will show up in the chat and you may proceed to answer questions and requests based on those outputs. An empty output usually means the code ran successfully. Things like charts and plots are supported by this interface, and they are visible to the user even if they are not visible to you. You can do multiple things and display multiple charts in one same Python code, if necessary.
    """
    empty_output = "Empty output. This normally means the code ran successfully."

    def execute(self, code):
        try:
            from langchain_experimental.utilities import PythonREPL
            repl = PythonREPL()
        except Exception as e:
            return f"ERROR: {e}"
        return repl.run(code.strip())
    
class FileShowInterface(Interface):
    name = "FILE_SHOW"
    explanation = """
    This interface allows you to show the contents of a file in the user's filesystem. The input of your command is the path to the file to be shown. The file will be shown with line numbers. Please avoid repeating the contents of the file in your message after using this interface, as the user will already see the contents of the file in the chat.

    As mentioned above, the output of the FILE_SHOW command is the selected file with its line numbers.

    It is advisable to run a FILE_SHOW before running any FILE_WRITE command (see the FILE_WRITE interface below).
    """

    def execute(self, code):
        try:
            file_path = code.strip()
            file_path = os.path.abspath(os.path.expanduser(file_path))
            with open(file_path, "r") as f: contents = f.read()
            self.meta['file_path'] = file_path
            result = f"File {file_path} (shown below with line numbers):"
            content_lines = contents.split(os.linesep)
            max_line_number_size = len(str(len(content_lines)))
            for (i, line) in enumerate(contents.split(os.linesep)):
                line_number = " " * (max_line_number_size - len(str(i + 1))) + str(i + 1)
                result += os.linesep + f"{line_number}  {line}"
            return result
        except Exception as e:
            return f"ERROR: {e}"
        
    def cleanup(self):
        file_paths = set()
        for bubble in reversed(self.convo.bubbles):
            if not bubble.meta or bubble.meta.get('interface') not in ["FILE_SHOW", "FILE_WRITE"]: continue
            if bubble.meta.get('cleaned_up'): break
            file_path = bubble.meta.get('file_path')
            if not file_path: continue
            if file_path in file_paths:
                bubble.doc.text = "[OUTPUT HIDDEN]"
                bubble.meta['cleaned_up'] = True
            else:
                file_paths.add(file_path)

class SearchInterface(Interface):
    name = "SEARCH"
    explanation = """
    This interface allows you to search the web for information. The input of your command is the search query. The output of your command is the search results, which may be a single string answering your query or a list of truncated results.
    """

    def execute(self, code):
        try:
            from langchain_community.utilities import SerpAPIWrapper
            search = SerpAPIWrapper()
            return search.run(code.strip())
        except Exception as e:
                return f"ERROR: {e}"


class FileWriteInterface(Interface):
    name = "FILE_WRITE"
    explanation = """
    This interface allows you to write a new file or replace the contents of a file in the user's filesystem. The first line of your command is the path to the file to be created or replaced. The second line is the range of file lines to be replaced, e.g. 10-20, or the word ALL. The new contents of the file or of the replaced lines should start on the next line. This will cause the file to be written to the filesystem of the user.

    The output of the FILE_WRITE command is the full selected file with its line numbers. Always refer to the latest output of the FILE_SHOW command or of the FILE_WRITE command to see the current contents of the file. This allows you to make iterative changes to a file by specifying the correct line numbers every time.

    For example, the command below creates a file with letters A-Z, one in each line, some of them skipped:

    [__FILE_WRITE__]
    path/to/file.txt
    A
    B
    (skipped some
     letters)
    I
    J
    (skipped some letters)
    [/__FILE_WRITE__]
    [OUTPUT]
    File written to path/to/file.txt (shown below with line numbers):
    1  A
    2  B
    3  (skipped some
    4   letters)
    5  I
    6  J
    7  (skipped some letters)
    [END OF OUTPUT]

    Then the command below inserts the missing letters C-H:

    [__FILE_WRITE__]
    path/to/file.txt
    3-4
    C
    D
    E
    F
    G
    H
    [/__FILE_WRITE__]
    [OUTPUT]
    File written to path/to/file.txt (shown below with line numbers):
     1  A
     2  B
     3  C
     4  D
     5  E
     6  F
     7  G
     8  H
     9  I
    10  J
    11  (skipped some letters)
    [END OF OUTPUT]

    Now if you want to insert a couple more letters after J, and keep the "(skipped some letters)" line, you must remember that you need to rewrite any line that you want to keep (because the FILE_WRITE interface always performs a replace operation). So you would do:

    [__FILE_WRITE__]
    path/to/file.txt
    11-11
    K
    L
    M
    (skipped some letters)
    [/__FILE_WRITE__]
    [OUTPUT]
    File written to path/to/file.txt (shown below with line numbers):
     1  A
     2  B
     3  C
     4  D
     5  E
     6  F
     7  G
     8  H
     9  I
    10  J
    11  K
    12  L
    13  M
    14  (skipped some letters)
    [END OF OUTPUT]
    """
    def execute(self, code):
        try:
            args = code.lstrip().split(os.linesep, 2)
            assert len(args) == 3, "Remember the first line of the FILE_WRITE arguments must be the file path, the second line is the line range (or the word ALL), and on the third line starts the new content of the file."
            # if len(args) == 1: args = args + ["ALL", ""]
            # elif len(args) == 2: args = args + [""]
            file_path, line_range, contents = args
            file_path = file_path.strip()
            file_path = os.path.abspath(os.path.expanduser(file_path))
            base_folder = os.path.dirname(file_path)
            if base_folder and not os.path.exists(base_folder): os.makedirs(base_folder)
            current_contents = None
            if os.path.exists(file_path):
                with open(file_path, "r") as f: current_contents = f.read()
            if line_range != "ALL":
                range = line_range.split("-")
                start_line, end_line = [int(i) for i in range] if len(range) == 2 else [int(line_range), int(line_range)]
                lines = current_contents.split(os.linesep) if current_contents else []
                lines = lines[:start_line - 1] + contents.strip(os.linesep).split(os.linesep) + lines[end_line:]
                contents = os.linesep.join(lines)
            with open(file_path, "w") as f: f.write(contents)
            self.meta['file_path'] = file_path
            result = f"File written to {file_path} (shown below with line numbers):"
            content_lines = contents.split(os.linesep)
            max_line_number_size = len(str(len(content_lines)))
            for (i, line) in enumerate(contents.split(os.linesep)):
                line_number = " " * (max_line_number_size - len(str(i + 1))) + str(i + 1)
                result += os.linesep + f"{line_number}  {line}"
            return result
        except Exception as e:
            return f"ERROR: {e}"
        
    def cleanup(self):
        file_paths = set()
        for bubble in reversed(self.convo.bubbles):
            if not bubble.meta or bubble.meta.get('interface') not in ["FILE_SHOW", "FILE_WRITE"]: continue
            if bubble.meta.get('cleaned_up'): break
            file_path = bubble.meta.get('file_path')
            if not file_path: continue
            if file_path in file_paths:
                bubble.doc.text = "[OUTPUT HIDDEN]"
                bubble.meta['cleaned_up'] = True
            else:
                file_paths.add(file_path)


                


