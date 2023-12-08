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
        self.system << """
        You are a useful AI assistant. You try to answer the user's questions and perform the tasks requested by the user.
        """
        if len(self.interfaces) > 0:
            self.system << """
            You are equipped with "interfaces" as described below. Do not limit yourself. These interfaces allow you to perform tasks that a normal LLM-based assistant would not be able to do.
            """
            for interface in self.interfaces:
                self.system << interface.explanation
            self.system << f"""
            Feel free to go step by step when following instructions from the user. It is ok to ask for clarification questions, or to use the interfaces provided to find out more information before performing an action.
            """

    # New method for updating context
    def update_context(self, new_context):
        """
        Updates the system's conversation context with new information.
        
        :param new_context: A string that contains the new context to be added.
        """
        self.system << new_context

    # ... Rest of the Convo class ...

# ... Rest of the file including other classes and methods ...
