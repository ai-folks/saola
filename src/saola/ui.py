import abc
import os
from rich.panel import Panel
from rich import print as rprint
from rich.markup import escape
from rich.prompt import Confirm
from uuid import uuid4
from saola.utils import _is_notebook
import time


# TODO: Make it so that stale conversation messages are clearly marked stale.

class UI(abc.ABC):
    # A UI is a bridge for the application to communicate with the user.
    def will_begin_interface_output(self, interface):
        # Called before an interface's output is displayed.
        pass
    def display_interface_output(self, output):
        # Displays an interface's output to the user.
        pass
    def safety_confirmation(self, name):
        # Asks the user a yes/no question and returns the answer.
        pass
    def no_safety_confirmation(self):
        # Return True always after any preparation for displaying results without a confirmation.
        pass
    def display_user_header(self):
        # Preparation for requesting the user's input.
        pass
    def supports_synchronous_user_input(self):
        # Returns True if the UI can get the user's input synchronously.
        pass
    def get_user_input(self):
        # Gets the user's input.
        pass
    def display_assistant_header(self):
        # Preparation for displaying the assistant's output.
        pass
    def append_to_assistant_output(self, author, chunk, ending):
        # Appends text to the assistant's output.
        pass
    def show_warning(self, text=None):
        # Shows a warning to the user.
        pass
    def show_info(self, text=None):
        # Shows an informational message to the user.
        pass

class ShellUI(UI):
    def display_interface_output(self, output):
        pass
        # rprint(Panel("[bright_magenta]" + escape(output) + "[/bright_magenta]", border_style="bright_magenta"))

    def safety_confirmation(self, name):
        print("")
        rprint(Panel("[red1] SAFETY CHECK [/red1]", border_style="red1"))
        return Confirm.ask(f"[red1] Execute {name} code? [/red1]")

    def no_safety_confirmation(self):
        print("")
        return True 

    def display_user_header(self):
        rprint(Panel("[bold green]USER (enter your question below)[/bold green]"))

    def supports_synchronous_user_input(self):
        return True

    def get_user_input(self):
        return input("")

    def display_assistant_header(self):
        rprint(Panel("[bold blue]ASSISTANT[/bold blue]"))

    def append_to_assistant_output(self, author, chunk, ending):
        print(chunk or "", end="\n" if ending else "")

    def show_warning(self, text=None):
        if text is None:
            rprint(Panel("[red1] [!] This assistant will be able to execute commands\n" +
                        "    on your shell when prompted. You will be asked to\n" +
                        "    confirm the execution of each of these commands.\n" + 
                        "    Please read each command and respond carefully.\n" +
                        "    Use at your own risk.[/red1]", border_style="red1"))
        else:
            rprint(Panel("[red1] " + text + "[/red1]", border_style="red1"))
        
    def show_info(self, text):
        rprint(Panel(text))


class NotebookUI(UI):
    SAOLA_OUTPUT_START = "```saola_output"
    SAOLA_OUTPUT_END = "<!-- end of saola_output -->"
    def will_begin_interface_output(self, interface):
        print(os.linesep + self.SAOLA_OUTPUT_START)

    def display_interface_output(self, output):
        # Does not actually print the output, as this is assumed to be printed during execution
        print(("" if output.endswith(os.linesep) else os.linesep) + "```\n" + self.SAOLA_OUTPUT_END)

    def safety_confirmation(self, name):
        from IPython.display import display, HTML
        display(HTML("""
        <script>
            saola.stopAssistantAnimations();
        </script>
        <button style="
                     padding: 0.7em;
                     padding-top: 0.5em;
                    background: #fff;
                    color: #4A5568;
                    margin-top: 0.5em;
                    border: 0px solid #A0AEC0;
                    box-shadow: 0 0 0 #BEE3F8;
                    transform: translateY(0);
                    border-radius: .5em;
                     font-size: 1.4vmin;font-family: 'Poppins', sans-serif;
                     "
                        onclick="
                        var _this = this;
                        setTimeout(function() {
                            cell = saola.getContainingCell(_this);
                            nextCell = cell.nextElementSibling;
                            saola.setCellText(nextCell, 'saola.user << True # Run the code above and handoff back to the Saola assistant', '');
                        }, 1);
                     ">
                <div style="display: inline-block;  vertical-align: middle;"><i class="gg-play-button-o"></i></div><div style="display: inline-block;  vertical-align: middle;">&nbsp;&nbsp;Run Code</div></button>
        """))
        return None

    def no_safety_confirmation(self):
        return True 

    def display_user_header(self):
        from IPython.display import display, HTML
        uuid = str(uuid4()).replace("-", "_")
        display(HTML("""
        <!--<link rel="stylesheet" href="https://unpkg.com/beautiful-markdown" />-->
        <link href="https://fonts.googleapis.com/css?family=Poppins:600&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark-dimmed.min.css">

        <style type="text/css">

        code.language-saola_output {
            background-color: #303030;
            border: 2px solid #000;
        }
            
        .saola-code-toggle + label {
            color: #404040;
            cursor: pointer;
            margin-left: 0.1em;
        }

        .saola-code-toggle + label + pre {
            display: none !important;
        }
                
        .saola-code-toggle:checked + label + pre {
            display: block !important;
        }

        .saola-markdown-rendered {
            padding-right: 25px;
            font-family: 'Arial', sans-serif;
            font-size: 1.1em;
        }
                     
        .saola-markdown-rendered-no-toggles > .saola-code-toggle {
            display: none;
        }
        
        .saola-markdown-rendered-no-toggles > .saola-code-toggle + label {
            display: none;
        }
                     
        code.hljs {
            border-radius: 0.3em;
        }

        .jp-WindowedPanel, .jp-Notebook-cell, #notebook-container {
            background: linear-gradient(90deg, #e3ffe7 0%, #d9e7ff 100%) !important; 
        }
        
        .gg-user {
            display: block;
            transform: scale(var(--ggs,1));
            box-sizing: border-box;
            width: 12px;
            height: 18px
        }
        .gg-user::after,
        .gg-user::before {
            content: "";
            display: block;
            box-sizing: border-box;
            position: absolute;
            border: 2px solid
        }
        .gg-user::before {
            width: 8px;
            height: 8px;
            border-radius: 30px;
            top: 0;
            left: 2px
        }
        .gg-user::after {
            width: 12px;
            height: 9px;
            border-bottom: 0;
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
            top: 9px
        }
        .gg-comment {
        box-sizing: border-box;
        position: relative;
        display: block;
        transform: scale(var(--ggs,1));
        width: 20px;
        height: 16px;
        border: 2px solid;
        border-bottom: 0;
        box-shadow:
        -6px 8px 0 -6px,
        6px 8px 0 -6px
        }

        .gg-comment::after,
        .gg-comment::before {
        content: "";
        display: block;
        box-sizing: border-box;
        position: absolute;
        width: 8px
        }

        .gg-comment::before {
        border: 2px solid;
        border-top-color: transparent;
        border-bottom-left-radius: 20px;
        right: 4px;
        bottom: -6px;
        height: 6px
        }

        .gg-comment::after {
        height: 2px;
        background: currentColor;
        box-shadow: 0 4px 0 0;
        left: 4px;
        top: 4px
        } 
                     
        .gg-sand-clock {
        box-sizing: border-box;
        position: relative;
        display: block;
        transform: scale(var(--ggs,1));
        width: 12px;
        height: 20px;
        border-top: 2px solid;
        border-bottom: 2px solid
        }

        .gg-sand-clock::after,
        .gg-sand-clock::before {
        content: "";
        display: block;
        box-sizing: border-box;
        position: absolute
        }

        .gg-sand-clock::before {
        border-top-left-radius: 14px;
        border-top-right-radius: 14px;
        bottom: -2px;
        width: 10px;
        height: 10px;
        border: 2px solid;
        left: 1px
        }

        .gg-sand-clock::after {
        width: 6px;
        height: 6px;
        border: 2px solid transparent;
        border-bottom-left-radius: 14px;
        border-bottom-right-radius: 14px;
        top: 0;
        left: 3px;
        box-shadow:
        0 0 0 2px,
        inset 2px 0 0
        } 



        .gg-play-button-o {
        box-sizing: border-box;
        position: relative;
        display: block;
        transform: scale(var(--ggs,1));
        width: 22px;
        height: 22px;
        border: 2px solid;
        border-radius: 20px
        }

        .gg-play-button-o::before {
        content: "";
        display: block;
        box-sizing: border-box;
        position: absolute;
        width: 0;
        height: 10px;
        border-top: 5px solid transparent;
        border-bottom: 5px solid transparent;
        border-left: 6px solid;
        top: 4px;
        left: 7px
        } 
                     
        @keyframes saolaSandClockAnimation {
            0% {
                transform: rotate(-30deg);
            }
            50% {
                transform: rotate(30deg);
            }
            100% {
                transform: rotate(-30deg);
            }
        }

        .gg-sand-clock {
            transform: translateY(5%);
            display: none;
        }
                     
        .saola-assistant-header-animated .gg-comment {
            display: none;
        }
                     
        .saola-assistant-header-animated .gg-sand-clock {
            animation: saolaSandClockAnimation 1s infinite;
            display: block;
        }
        </style>
        <div style="padding: 0.7em;
                    background: linear-gradient(90deg, #bdd6ff 0%, #d9e7ff 100%);
                    color: #4A5568;
                    margin-top: 0.5em;
                    border: 0px solid #A0AEC0;
                    box-shadow: 0 0 0 #BEE3F8;
                    transform: translateY(0);
                        border-radius: .5em;
                     "
                id="user_header""" + uuid + """">
            <div style="font-size: 2vmin;font-family: 'Poppins', sans-serif;"><div style="display: inline-block"><i class="gg-user"></i></div>&nbsp;&nbsp;USER</div>

        </div>
        
        <script>
            function addGlobalSaolaTooling(marked) {
                if (window.saola) return;
                window.saola = {};

                // -----------------------------
                // OUTPUT OBSERVER
                // -----------------------------

                function processPlainTextOutput(element) {
                    element.style.display = 'none';
                    var prev = element.previousElementSibling;
                    if (!prev || !prev.classList.contains('saola-markdown-rendered')) {
                        prev = document.createElement('div');
                        markdownContent = element.textContent;
                        markdownContent = markdownContent.replace(/\\n?\\[(__\\w+__)\\]\\n?/g, (match, p1) => "\\n```" + p1.toLowerCase() + "\\n");
                        markdownContent = markdownContent.replace(/\\n?\\[\\/(__\\w+__)\\]\\n?/g, "\\n```\\n");
                        markdownContent = markdownContent.replace(/^\\n/g, "");
                        markdownContent = markdownContent.replace(/\\n$/g, "");
                        SAOLA_OUTPUT_START = '""" + self.SAOLA_OUTPUT_START + """';
                        SAOLA_OUTPUT_END = '""" + self.SAOLA_OUTPUT_END + """';
                        // Finds all lines that match exactly SAOLA_OUTPUT_START or SAOLA_OUTPUT_END
                        // - If the first ocurrence is SAOLA_OUTPUT_END, it removes it
                        // - If the last ocurrence is SAOLA_OUTPUT_START, it removes it
                        var lines = markdownContent.split('\\n');
                        var startLineIndexes = lines.map((line, index) => line === SAOLA_OUTPUT_START ? index : -1).filter(index => index !== -1);
                        var endLineIndexes = lines.map((line, index) => line === SAOLA_OUTPUT_END ? index : -1).filter(index => index !== -1);
                        if (endLineIndexes.length > 0 && (startLineIndexes.length === 0 || endLineIndexes[0] < startLineIndexes[0])) {
                            if (endLineIndexes[0] == 1) {
                                lines.splice(endLineIndexes[0] - 1, 2);  // Removes the line before and the line of SAOLA_OUTPUT_END
                            } else {
                                lines.splice(0, 0, SAOLA_OUTPUT_START);  // Adds the line of SAOLA_OUTPUT_START
                            }
                        }
                        // We need to compute the indexes again, because the array has changed
                        startLineIndexes = lines.map((line, index) => line === SAOLA_OUTPUT_START ? index : -1).filter(index => index !== -1);
                        endLineIndexes = lines.map((line, index) => line === SAOLA_OUTPUT_END ? index : -1).filter(index => index !== -1);
                        if (startLineIndexes.length > 0 && (endLineIndexes.length === 0 || startLineIndexes[startLineIndexes.length - 1] > endLineIndexes[endLineIndexes.length - 1])) {
                            if (startLineIndexes[startLineIndexes.length - 1] == lines.length - 1) {
                                lines.splice(startLineIndexes[startLineIndexes.length - 1], 1);
                            } else {
                                lines.splice(lines.length, 0, '```\\n' + SAOLA_OUTPUT_END);
                            }
                        }
                        markdownContent = lines.join('\\n');
                        prev.innerHTML = marked.parse(markdownContent);
                        function addToggle(codeBlock) {
                            elementId = 'saola-code-toggle-' + Math.random().toString(36).substring(7);
                            var toggle = document.createElement('input');
                            toggle.id = elementId;
                            toggle.classList.add('saola-code-toggle');
                            toggle.type = 'checkbox';
                            toggle.checked = false;
                            var toggleLabel = document.createElement('label');
                            toggleLabel.innerText = 'Expand Code';
                            toggleLabel.htmlFor = elementId;
                            codeBlock.parentNode.parentNode.insertBefore(toggle, codeBlock.parentNode);
                            codeBlock.parentNode.parentNode.insertBefore(toggleLabel, codeBlock.parentNode);
                        }
                        prev.querySelectorAll('code.language-__python__, code.language-__shell__').forEach(addToggle);
                        prev.classList.add('saola-markdown-rendered');
                        prev.classList.add('saola-markdown-rendered-no-toggles');
                        element.parentNode.insertBefore(prev, element);
                    }
                }

                function getAddedDescendants(mutation, pathClasses, innerTagName, targetParentClass=null) {
                    if (mutation.type !== 'childList') return [];
                    if (pathClasses.length === 0) return [];
                    if (targetParentClass && !mutation.target.classList.contains(targetParentClass)) return [];
                    if (!mutation.target.classList.contains(pathClasses[0])) return mutation.target.tagName === innerTagName ? [mutation.target] : [];
                    var nodes = Array.from(mutation.addedNodes)
                    if (pathClasses.length === 1) return nodes.filter(node => node.tagName === innerTagName);
                    var pathIndex = 1;
                    nodes = nodes.filter(node => node.classList.contains(pathClasses[1]));
                    while (pathIndex < pathClasses.length - 1) {
                        pathIndex++;
                        nodes = nodes.flatMap(node => Array.from(node.children).filter(child => child.classList.contains(pathClasses[pathIndex])));
                    }
                    return nodes.flatMap(node => Array.from(node.children).filter(child => child.tagName === innerTagName));
                }

                // Define the callback function to execute when mutations are observed
                const callback = function(mutationsList, observer) {
                    for (const mutation of mutationsList) {
                        // Jupyter Notebook & JupyterLab
                        pres0 = getAddedDescendants(mutation, ['jp-OutputArea-output'], 'PRE');
                        pres1 = getAddedDescendants(mutation, ['jp-OutputArea', 'jp-OutputArea-child', 'jp-OutputArea-output'], 'PRE');
                        // NbClassic
                        pres2 = getAddedDescendants(mutation, ['output', 'output_area', 'output_subarea'], 'PRE');
                        pres3 = getAddedDescendants(mutation, [], 'PRE', 'output_subarea');
                        pres = pres0.concat(pres1).concat(pres2).concat(pres3);
                        pres.forEach(processPlainTextOutput);
                    }
                };

                const observer = new MutationObserver(callback);
                observer.observe(document.body, { childList: true, subtree: true });
                document.querySelectorAll('.jp-OutputArea-output > pre').forEach(processPlainTextOutput);
                document.querySelectorAll('.output_subarea > pre').forEach(processPlainTextOutput);

                // -----------------------------
                // GLOBAL FUNCTIONS
                // -----------------------------

                function getContainingCell(element) {
                    return element.closest('.jp-Notebook-cell') ?? element.closest('.code_cell');
                }

                function _setElementText(element, beforeCaretText, afterCaretText, ifEmpty) {
                    if (ifEmpty && element.textContent.trim() !== '') return;
                    element.focus();
                    element.textContent = beforeCaretText + afterCaretText;
                    const range = document.createRange();
                    const selection = window.getSelection();
                    const position = beforeCaretText.length;
                    range.setStart(element.firstChild, position);
                    range.collapse(true); // Collapses the Range to one of its boundary points
                    selection.removeAllRanges();
                    selection.addRange(range);
                }

                function _setCodeMirrorText(codeMirror, beforeCaretText, afterCaretText, ifEmpty) {
                    if (ifEmpty && codeMirror.getValue().trim() !== '') return;
                    codeMirror.setValue(beforeCaretText + afterCaretText);
                    const beforeCaretLines = beforeCaretText.split('\\n');
                    const line = beforeCaretLines.length - 1;
                    const ch = beforeCaretLines[beforeCaretLines.length - 1].length;
                    codeMirror.setCursor({line, ch});
                    codeMirror.focus();
                }

                function setCellText(cell, beforeCaretText, afterCaretText, ifEmpty=true) {
                    var content = cell.querySelector('.cm-content');
                    if (content) {
                        _setElementText(content, beforeCaretText, afterCaretText, ifEmpty);
                    } else {
                        var codeMirror = cell.querySelector('.CodeMirror').CodeMirror;
                        if (codeMirror) {
                            _setCodeMirrorText(codeMirror, beforeCaretText, afterCaretText, ifEmpty);
                        }
                    }
                }

                function stopAssistantAnimations() {
                    setTimeout(function() {
                        // Get rid of all classes saola-markdown-rendered-no-toggles and saola-assistant-header-animated
                        document.querySelectorAll('.saola-markdown-rendered-no-toggles').forEach(function(element) {
                            element.classList.remove('saola-markdown-rendered-no-toggles');
                        });
                        document.querySelectorAll('.saola-assistant-header-animated').forEach(function(element) {
                            element.classList.remove('saola-assistant-header-animated');
                        });
                    }, 1);
                }

                window.saola.getContainingCell = getContainingCell;
                window.saola.setCellText = setCellText;
                window.saola.stopAssistantAnimations = stopAssistantAnimations;
            }

            window.markedModuleImported""" + uuid + """ = function(marked) {
                addGlobalSaolaTooling(marked);
                saola.stopAssistantAnimations();
                setTimeout(function() {
                    var header = document.getElementById('user_header""" + uuid + """');
                    cell = saola.getContainingCell(header);
                    nextCell = cell.nextElementSibling;
                    saola.setCellText(nextCell, '# Enter some text and run this cell to talk to your Saola assistant\\nsaola.user << \"\"\"\\n', '\\n\"\"\"');
                }, 1);
            };
        </script>
                     
        <script type="module">
            import { Marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
            import { markedHighlight } from "https://cdn.jsdelivr.net/npm/marked-highlight@2.1.1/+esm";
            import hljs from "https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/+esm";
            import python from 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/es/languages/python.min.js';
            import bash from 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/es/languages/bash.min.js';
            import text from 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/es/languages/plaintext.min.js';
            hljs.registerLanguage('python', python);
            hljs.registerLanguage('__python__', python);
            hljs.registerLanguage('shell', bash);
            hljs.registerLanguage('__shell__', bash);
            hljs.registerLanguage('text', text);
            hljs.registerLanguage('plaintext', text);
            hljs.registerLanguage('saola_output', text);
            var marked = new Marked(
                markedHighlight({
                    langPrefix: 'hljs language-',
                    highlight(code, lang, info) {
                    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                    return hljs.highlight(code, { language }).value;
                    }
                })
            )
            window.markedModuleImported""" + uuid + """(marked);
        </script>
        """))


    def supports_synchronous_user_input(self):
        return False

    def get_user_input(self):
        raise NotImplementedError("The Notebook UI does not support synchronous user input.")

    def display_assistant_header(self):
        from IPython.display import display, HTML
        display(HTML("""
        <div class="saola-assistant-header-animated"
                style="padding: 0.7em;
                    background: linear-gradient(90deg, #bff3cf 0%, #d9e7ff 100%);
                    color: #4A5568;
                    border: 0px solid #A0AEC0;
                    margin-top: 1em;
                    margin-bottom: 0.3em;
                    box-shadow: 0 0 0 #BEE3F8;
                    transform: translateY(0);
                        border-radius: .5em;
                     ">
            <div style="font-size: 2vmin;font-family: 'Poppins', sans-serif;"><div style="display: inline-block"><i class="gg-comment"></i><i class="gg-sand-clock"></i></div>&nbsp;&nbsp;ASSISTANT</div>
        </div>
        """))
        # rprint(Panel("[bold blue]ASSISTANT[/bold blue]"))

    def append_to_assistant_output(self, author, chunk, ending):
        print(chunk or "", end="\n" if ending else "")

    def show_warning(self, text=None):
        from IPython.display import display, HTML
        text = text or "⚠️ This assistant will be able to execute code on your behalf. You may be asked to confirm the execution of each of these commands. Please read each command and respond carefully. Use at your own risk."
        display(HTML(f"""
        <div style="padding: 0.7em;
                    background: #ee5050;
                    color: #fff;
                    font-size: 1.5vmin;
                    border: 0px solid #A0AEC0;
                    box-shadow: 0 0 0 #BEE3F8;
                    transform: translateY(0);
                        border-radius: .5em;
                     ">
            {text}
        </div>
        """))
        
    def show_info(self, text):
        from IPython.display import display, HTML
        display(HTML(f"""
        <div style="padding: 0.7em;
                    background: #aaaaaa;
                    color: #fff;
                    font-size: 1.5vmin;
                    border: 0px solid #A0AEC0;
                    box-shadow: 0 0 0 #BEE3F8;
                    transform: translateY(0);
                        border-radius: .5em;
                     ">
            {text}
        </div>
        """))


DefaultUI = NotebookUI if _is_notebook() else ShellUI
    