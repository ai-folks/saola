import abc
from rich.panel import Panel
from rich import print as rprint
from rich.markup import escape
from rich.prompt import Confirm

def _is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__  # type: ignore
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter

class UI(abc.ABC):
    # A UI is a bridge for the application to communicate with the user.
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
    def display_interface_output(self, output):
        pass
        # from IPython.display import display, Markdown
        # display(Markdown(f'```\n{output}\n```'))

    def safety_confirmation(self, name):
        from IPython.display import display, HTML
        display(HTML("""
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
                    setTimeout(function() {
                    var cell_index = Jupyter.notebook.get_selected_index() + 1;
                    var cell = Jupyter.notebook.get_cell(cell_index);
                    var current_cell_text = cell.get_text();
                    var new_cell_text = '# This lets me run the code above\\nsaola.user << True';
                    if (current_cell_text === '') {
                        cell.set_text(new_cell_text);
                        cell.code_mirror.focus();
                        cell.render();
                    }
                    cell.code_mirror.focus();
                     }, 100);
                     ">
                <div style="display: inline-block;  vertical-align: middle;"><i class="gg-play-button-o"></i></div><div style="display: inline-block;  vertical-align: middle;">&nbsp;&nbsp;Run Code</div></button>
        """))
        return None

    def no_safety_confirmation(self):
        return True 

    def display_user_header(self):
        from IPython.display import display, HTML
        display(HTML("""
        <!--<link rel="stylesheet" href="https://unpkg.com/beautiful-markdown" />-->
        <link href="https://fonts.googleapis.com/css?family=Poppins:600&display=swap" rel="stylesheet">

        <style type="text/css">
        .markdown-rendered > pre {
            background-color: rgba(0, 0, 0, 0.05) !important;
            padding: 1em !important; 
        }

        #notebook-container {
            background: linear-gradient(90deg, #e3ffe7 0%, #d9e7ff 100%);
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
        </style>
        <div style="padding: 0.7em;
                    background: #bdd6ff;
                    color: #4A5568;
                    margin-top: 0.5em;
                    border: 0px solid #A0AEC0;
                    box-shadow: 0 0 0 #BEE3F8;
                    transform: translateY(0);
                        border-radius: .5em;
                     ">
            <div style="font-size: 2vmin;font-family: 'Poppins', sans-serif;"><div style="display: inline-block"><i class="gg-user"></i></div>&nbsp;&nbsp;USER</div>

        </div>
        <script>
        var cell_index = Jupyter.notebook.get_selected_index();
        var cell = Jupyter.notebook.get_cell(cell_index);
        var current_cell_text = cell.get_text();
        var new_cell_text = "# Type your message below\\nsaola.user << \\\"\\\"\\\"\\n\\n\\\"\\\"\\\"";
        // Only if cell text is empty
        if (current_cell_text === "" || current_cell_text === new_cell_text) {
            cell.set_text(new_cell_text);
            cell.code_mirror.focus();
            cell.code_mirror.setCursor({line: 2, ch: 0})
            cell.render();
        }
        cell.code_mirror.focus();
        // Jupyter.notebook.select(cell_index);
        // Jupyter.notebook.edit_mode();
        </script>
                     

        <script>
            if (document.addedMarkdownObserver === undefined) {
                
                markdown = requirejs("base/js/markdown")
                
                function startMarkdownRendering() {
                    // Function to create/update the markdown display element
                    function renderMarkdown(preElement) {
                     
                        preElement.style.display = 'none';
                     
                        let markdownContent = preElement.innerText;
                        let markdownDisplay = preElement.previousElementSibling;
                        
                        // Check if the markdown display element already exists
                        if (!markdownDisplay || markdownDisplay.className !== 'markdown-rendered') {
                            // Create a new markdown display element if it doesn't exist
                            markdownDisplay = document.createElement('div');
                            markdownDisplay.className = 'markdown-rendered';
                            preElement.parentNode.insertBefore(markdownDisplay, preElement);
                        }
                        
                        markdownContent = markdownContent.replace(/\\n?\\[(\\w+)\\]\\n?/g, (match, p1) => "\\n```" + p1.toLowerCase().replaceAll("_", "") + "\\n");
                        markdownContent = markdownContent.replace(/\\n?\\[\\/(\\w+)\\]\\n?/g, "\\n```\\n");

                        // Number of lines that start with ```:
                        let numCodeBlocks = (markdownContent.match(/```/g) || []).length;
                        // If the number of code blocks is odd, add a closing ```
                        if (numCodeBlocks % 2 === 1) { markdownContent += "\\n```"; }

                        // Update the markdown display element with rendered content
                        markdown.render(markdownContent, {with_math: true, clean_tables: true, sanitize: true}, function (err, html) { 
                            // console.log(html);
                            if (html !== undefined && html !== null) {
                                // Remove all children first:
                                while (markdownDisplay.firstChild) {
                                    markdownDisplay.removeChild(markdownDisplay.firstChild);
                                }
                                html.appendTo($(markdownDisplay));
                                // markdownDisplay.appendChild(html);
                            }
                         })
                    }

                    // Set up a MutationObserver to watch for changes in the DOM
                    const observer = new MutationObserver((mutationsList) => {
                    for (let mutation of mutationsList) {
                        // console.log("MUTATION!")
                        // console.log(mutation)
                        if (mutation.type === 'childList' && mutation.target.tagName === 'PRE'
                            && mutation.target.parentNode.classList.contains('output_subarea')) {
                            renderMarkdown(mutation.target);
                        } else if (mutation.type == 'childList' && mutation.target.tagName === 'DIV'
                                   && (mutation.target.classList.contains('output_subarea')
                                       || mutation.target.classList.contains('output_area')
                                       || mutation.target.classList.contains('output'))) {
                            mutation.target.querySelectorAll('pre').forEach(preElement => {
                                renderMarkdown(preElement);
                            });
                        }
                    }
                    });

                    // Observe the document body for changes in child list and character data
                    observer.observe(document.body, { childList: true, subtree: true, characterData: true });

                    // Initial rendering for existing `pre` elements
                    document.querySelectorAll('div.output_subarea > pre').forEach(preElement => {
                        renderMarkdown(preElement);
                    });
                }
                
                startMarkdownRendering();    
            }

            document.addedMarkdownObserver = true;
        </script>





        """))


    def supports_synchronous_user_input(self):
        return False

    def get_user_input(self):
        raise NotImplementedError("The Notebook UI does not support synchronous user input.")

    def display_assistant_header(self):
        from IPython.display import display, HTML
        display(HTML("""
        <div style="padding: 0.7em;
                    background: #bff3cf;
                    color: #4A5568;
                    border: 0px solid #A0AEC0;
                    margin-top: 1em;
                    margin-bottom: 0.3em;
                    box-shadow: 0 0 0 #BEE3F8;
                    transform: translateY(0);
                        border-radius: .5em;
                     ">
            <div style="font-size: 2vmin;font-family: 'Poppins', sans-serif;"><div style="display: inline-block"><i class="gg-comment"></i></div>&nbsp;&nbsp;ASSISTANT</div>
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
    