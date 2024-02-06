# Saola - A Powerful AI Assistant Framework

**Saola is an AI assistant**, as well as an open-source Python module that enables developers to build their own AI assistants. Unlike other frameworks, Saola leverages external interfaces within the assistant's own messages. This conversational paradigm enables it to perform more complex tasks that may involve diverse tooling or user input, after minimal prompting.

In the example below, the default Saola assistant is asked to _show three Canadian cities on a map with the name and age of their current mayors_. Saola breezes through multiple web searches, troubleshoots an API error, and completes the task autonomously. State-of-the-art assistants like ChatGPT Plus often struggle with this type of task, giving up easily and inserting placeholder data whenever first attempts fail.

https://github.com/ai-folks/saola/assets/8546027/e6ec2204-824c-4e49-828f-70361c6836a7

## Getting Started

To install Saola simply do:

```bash
pip install git+https://github.com/ai-folks/saola.git@2.1.0
```

And to try out the default Saola assistant (with `SHELL`, `FILE_WRITE` and `PYTHON` interfaces), do:

```bash
python -m saola.start
```

Or in a Python console or Jupyter notebook:

```python
import saola
saola.start()  # Alternatively saola.start(safety_checks=False) (use this at your own risk)
```

**Disclaimer**: This assistant is capable of executing shell commands and writing to files (you will be asked to confirm each action if you do not disable safety checks). It is intended for responsible use and should be employed with an understanding of the potential actions taken by the assistant.

## Development - Assistant Without Interfaces

The simplest example of a Saola assistant is one that mirrors the underlying LLM exactly (no special functionality, no interfaces):

```python
from saola.convo import Convo
from saola.model import OpenAIGPT4

Convo(OpenAIGPT4(api_key=input("OpenAI API Key: "))).loop()
```

## Development - Assistant With Interfaces

### Assistant With Built-In Terminal Access

This module ships with a built-in interface that enables an assistant to access the user's shell, as well as an interface that allows the assistant to write a new file or overwrite an existing one, as requested by the user. To test these capabilities, initiate an `Convo` loop as below:

```python
from saola.convo import Convo, ShellInterface, FileShowInterface, FileWriteInterface
from saola.model import OpenAIGPT4

Convo(
    OpenAIGPT4(api_key=input("OpenAI API Key: ")),
    interfaces=[ShellInterface, FileShowInterface, FileWriteInterface]
).loop()
```

Alternatively, you can initiate a conversation that leverages all or most of Saola's built-in functionalities as follows:

```bash
python -m saola.start
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

[__SHELL__]
ls ~/Documents
[/__SHELL__]
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

### Updating The System Prompt

You can edit the assistant's system prompt before starting your conversation. This functionality is particularly useful for providing the assistant with persistent information or special instructions.

For instance, if you want the assistant to use Canadian spelling of words in your conversation:

```python
from saola.convo import Convo
from saola.model import OpenAIGPT4

# Create a conversation instance
conversation = Convo(OpenAIGPT4(api_key=input("OpenAI API Key: ")))
conversation.system << 'Use Canadian spelling of words in this conversation.'
conversation.loop()
```

### Assistant With A Custom Interface

Say you wish to enable your assistant to exit the program on command. You can do this by creating a custom interface like the one below, and initiating the conversation loop:

```python
from saola.convo import Convo, Interface
from saola.model import OpenAIGPT4
import os

class ExitInterface(Interface):
    name = "EXIT"
    explanation = "This interface allows you exit the chat at any time."
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

[__EXIT__] [/__EXIT__]
%
```

</details>

## Custom UIs

A custom UI may be constructed by subclassing the `UI` class. Currently there is a `ShellUI` and a `NotebookUI`. Details and custom UI examples to come.
