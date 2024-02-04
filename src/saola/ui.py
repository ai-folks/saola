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
    def safety_confirmation(self, question):
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

class ShellUI(UI):
    def display_interface_output(self, output):
        rprint(Panel("[bright_magenta]" + escape(output) + "[/bright_magenta]", border_style="bright_magenta"))

    def safety_confirmation(self, question):
        print("")
        rprint(Panel("[red1] SAFETY CHECK [/red1]", border_style="red1"))
        return Confirm.ask(f"[red1] {question} [/red1]")

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


class NotebookUI(UI):
    def display_interface_output(self, output):
        rprint(Panel("[bright_magenta]" + escape(output) + "[/bright_magenta]", border_style="bright_magenta"))

    def safety_confirmation(self, question):
        print("")
        rprint(Panel("[red1] SAFETY CHECK [/red1]", border_style="red1"))
        return Confirm.ask(f"[red1] {question} [/red1]")

    def no_safety_confirmation(self):
        print("")
        return True 

    def display_user_header(self):
        rprint(Panel("[bold green]USER (type saola.convo << \"your message\")[/bold green]"))
        # Add a JavaScript code that finds the next cell and focuses on it,
        # and sets the text to 'saola.convo << """\n\n"""' and places the caret between the line breaks
        from IPython.display import display, HTML
        display(HTML("""
        <script>
        var cell_index = Jupyter.notebook.get_selected_index();
        var cell = Jupyter.notebook.get_cell(cell_index);
        cell.set_text("saola.convo << \\\"\\\"\\\"\\n\\n\\\"\\\"\\\"");
        cell.render();
        Jupyter.notebook.select(cell_index);
        Jupyter.notebook.edit_mode();
        </script>
        """))
        # display(HTML("""
        # <script>
        # var cell = Jupyter.notebook.get_selected_index() + 1;
        # Jupyter.notebook.select(cell);
        # Jupyter.notebook.edit_mode();
        # </script>
        # """))


    def supports_synchronous_user_input(self):
        return False

    def get_user_input(self):
        raise NotImplementedError("The Notebook UI does not support synchronous user input.")

    def display_assistant_header(self):
        rprint(Panel("[bold blue]ASSISTANT[/bold blue]"))

    def append_to_assistant_output(self, author, chunk, ending):
        print(chunk or "", end="\n" if ending else "")


DefaultUI = NotebookUI if _is_notebook() else ShellUI
    