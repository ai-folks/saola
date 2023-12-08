# Saola - A Simple Framework For Building Powerful AI Assistants

Saola is an open-source Python module that enables developers to **build their own AI assistant** upon existing Large Language Model (LLM) APIs, by writing very little additional code. Saola conversations **function almost exactly like conversations with the underlying LLMs**. The only difference is that Saola assistants can be configured to **leverage certain _interfaces_** by way of special syntaxes.

To install Saola simply do:

```bash
pip install git+https://github.com/ai-folks/saola.git@0.1.3
```

## Assistant Without Interfaces

The simplest example of a Saola assistant is one that mirrors the underlying LLM exactly (no special functionality, no interfaces):

```python
from saola.convo import Convo
from saola.model import OpenAIGPT4

Convo(OpenAIGPT4(api_key=input("OpenAI API Key: "))).loop()
```

## Assistant With Interfaces

### Assistant With Built-In Terminal Access

This module ships with a built-in interface that enables an assistant to access the user's shell, as well as an interface that allows the assistant to write a new file or overwrite an existing one, as requested by the user. To test these capabilities, initiate an `Convo` loop as below:

```python
from saola.convo import Convo, ShellInterface, FileWriteInterface
from saola.model import OpenAIGPT4

Convo(
    OpenAIGPT4(api_key=input("OpenAI API Key: ")),
    interfaces=[ShellInterface, FileWriteInterface]
).loop()
```

Alternatively, you can initiate a conversation that leverages all or most of Saola's built-in functionalities as follows:

```bash
python -m saola.demo_loop
```

Every time the assistant tries to run a command or write to a file, you will be prompted to confirm this action. You can optionally specify `safety_checks=False` on the `Convo` initializer to bypass these prompts.

**Disclaimer**: This assistant is capable of executing shell commands and writing to files. It is intended for responsible use and should be employed with an understanding of the potential actions taken by the assistant.

A conversation with this assistant may look like this:

<details>
<summary>Show/Hide Example</summary>
  
```
% python assistant_with_terminal_access.py
OpenAI API Key: abc-ABC1234567890
╭─────────────────────────────────────────────────────────────────────────────────────────────╮
│ USER (enter your question below)                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
list the files in my documents folder and tell me if any files there appear to be duplicates of
each other
╭─────────────────────────────────────────────────────────────────────────────────────────────╮
│ ASSISTANT                                                                                   │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
Sure, I can help you with that. To begin, I will list the files in your Documents folder and
then check for duplicates. Let's start by listing the files.

$> ls ~/Documents
╭─────────────────────────────────────────────────────────────────────────────────────────────╮
│ ...                                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
Now that we have the list of files in the Documents folder, let's analyze and look for
potential duplicates. Duplicates can be identified by their names or content, and since I don't
have the ability to compare the content of the files directly, I'll look for files with
identical or similar names that might indicate that they are duplicates.

Based on the file list, here are some files that have similar names and may be duplicates or
variations of each other:

...

These files have similar names that suggest they may be duplicates or related versions. If you
want to confirm whether they are true duplicates (by content), I can compare the hash values of
these pairs of files. This would help us confirm if they have identical content. Would you like
to proceed with this approach?
```

</details>

### Context Management with `update_context()`

As of the latest update, we've introduced the `update_context()` method to enable maintainers and developers to dynamically set or update the assistant's context during a conversation. This method is particularly useful for providing the assistant with persistent information or special instructions.

For instance, if you want the assistant to remember to run server processes in a "no hang up" mode, you could introduce this context as follows:

```python
from saola.convo import Convo
from saola.model import OpenAIGPT4

# Create a conversation instance
conversation = Convo(OpenAIGPT4(api_key=input("OpenAI API Key: ")))

# Context to run server processes in a "no hang up" mode
additional_context = """Remember to run server processes in a "no hang up" mode."""

# Update the conversation context
conversation.update_context(additional_context)

# Continue the conversation loop with the new context
conversation.loop()
```

By using `update_context()`, you ensure that your assistant's responses and actions take into account this specific directive throughout the interaction.



### Assistant With A Custom Interface

Say you wish to enable your assistant to exit the program on command. You can do this by creating a custom interface like the one below, and initiating the conversation loop:

```python
from saola.convo import Convo, Interface
from saola.model import OpenAIGPT4
import os

class ExitInterface(Interface):
    name = "EXIT"
    pattern_start = "{EXIT}"
    pattern_end = os.linesep
    explanation = "Whenever asked by the user, you may exit the chat by typing {EXIT} in its own line of text."
    safety_checks = False

    def execute(self, code):
        exit(0)

Convo(
    OpenAIGPT4(api_key=input("OpenAI API Key: ")),
    interfaces=[ExitInterface]
).loop()
```

A conversation with this assistant may look like this:

<details>
<summary>Show/Hide Example</summary>
  
```
% python assistant_that_can_exit_the_chat.py
OpenAI API Key: abc-ABC1234567890
╭────────────────────────────────────────────────────────────────────────────────────────────╮
│ USER (enter your question below)                                                           │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
Hi!
╭────────────────────────────────────────────────────────────────────────────────────────────╮
│ ASSISTANT                                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
Hello! How can I assist you today?
╭────────────────────────────────────────────────────────────────────────────────────────────╮
│ USER (enter your question below)                                                           │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
Please say "bye" and end the chat. Thanks.
╭────────────────────────────────────────────────────────────────────────────────────────────╮
│ ASSISTANT                                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
Bye! It was nice assisting you. 
{EXIT}
%
```

</details>

## Custom UIs

A custom UI may be constructed by subclassing the `UI` class. Details and examples to come.