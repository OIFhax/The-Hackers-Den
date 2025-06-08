"""
title: Manus Agent
author: Manus Team
author_url: https://manus.ai
description: A tool that provides autonomous agent capabilities similar to Manus AI
version: 0.1.0
required_open_webui_version: 0.4.0
requirements: requests
licence: MIT
"""

import os
import json
import requests
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

class Tools:
    def __init__(self):
        """Initialize the Manus Agent Tool."""
        self.valves = self.Valves()
        # Disable built-in citations to use our own
        self.citation = False
    
    class Valves(BaseModel):
        web_search_enabled: bool = Field(True, description="Enable web search capabilities")
        file_operations_enabled: bool = Field(True, description="Enable file system operations")
        shell_operations_enabled: bool = Field(True, description="Enable shell command execution")
        browser_operations_enabled: bool = Field(True, description="Enable browser operations")
    
    class UserValves(BaseModel):
        agent_name: str = Field("Manus", description="Name of the agent")
        agent_personality: str = Field("helpful", description="Personality of the agent (helpful, creative, precise)")
    
    def message_notify(self, text: str, attachments: Optional[List[str]] = None, __event_emitter__=None) -> str:
        """
        Send a message to the user without requiring a response.
        
        Args:
            text: Message text to display to user
            attachments: (Optional) List of attachments to show to user, can be file paths or URLs
            
        Returns:
            Confirmation message
        """
        if __event_emitter__:
            __event_emitter__({"type": "message", "data": {"text": text, "attachments": attachments or []}})
        
        return f"Message sent: {text[:30]}..." if len(text) > 30 else f"Message sent: {text}"
    
    def message_ask(self, text: str, attachments: Optional[List[str]] = None, suggest_user_takeover: str = "none", __event_call__=None) -> str:
        """
        Ask user a question and wait for response.
        
        Args:
            text: Question text to present to user
            attachments: (Optional) List of question-related files or reference materials
            suggest_user_takeover: (Optional) Suggested operation for user takeover
            
        Returns:
            User's response
        """
        if __event_call__:
            response = __event_call__("ask", {"text": text, "attachments": attachments or [], "suggest_user_takeover": suggest_user_takeover})
            return response.get("text", "No response received")
        
        return "User response would be returned here"
    
    def file_read(self, file: str, start_line: Optional[int] = None, end_line: Optional[int] = None, sudo: bool = False, __event_emitter__=None) -> str:
        """
        Read file content.
        
        Args:
            file: Absolute path of the file to read
            start_line: (Optional) Starting line to read from, 0-based
            end_line: (Optional) Ending line number (exclusive)
            sudo: (Optional) Whether to use sudo privileges
            
        Returns:
            File content as text
        """
        if __event_emitter__:
            __event_emitter__({"type": "status", "data": {"text": f"Reading file: {file}"}})
        
        try:
            if not os.path.exists(file):
                return f"File not found: {file}"
            
            with open(file, 'r', encoding='utf-8') as f:
                if start_line is not None or end_line is not None:
                    lines = f.readlines()
                    start = start_line or 0
                    end = end_line or len(lines)
                    return ''.join(lines[start:end])
                else:
                    return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def file_write(self, file: str, content: str, append: bool = False, leading_newline: bool = False, trailing_newline: bool = True, sudo: bool = False, __event_emitter__=None) -> str:
        """
        Overwrite or append content to a file.
        
        Args:
            file: Absolute path of the file to write to
            content: Text content to write
            append: (Optional) Whether to use append mode
            leading_newline: (Optional) Whether to add a leading newline
            trailing_newline: (Optional) Whether to add a trailing newline
            sudo: (Optional) Whether to use sudo privileges
            
        Returns:
            Status message
        """
        if __event_emitter__:
            __event_emitter__({"type": "status", "data": {"text": f"{'Appending to' if append else 'Writing'} file: {file}"}})
        
        try:
            directory = os.path.dirname(file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            mode = 'a' if append else 'w'
            with open(file, mode, encoding='utf-8') as f:
                if leading_newline:
                    f.write('\n')
                f.write(content)
                if trailing_newline:
                    f.write('\n')
            
            return f"Successfully {'appended to' if append else 'wrote to'} {file}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"
    
    def search_web(self, query: str, __event_emitter__=None) -> str:
        """
        Search the web for information.
        
        Args:
            query: The search query
            
        Returns:
            Search results as text
        """
        if __event_emitter__:
            __event_emitter__({"type": "status", "data": {"text": f"Searching the web for: {query}"}})
        
        try:
            # This is a simulated web search
            # In a real implementation, you would use a search API
            results = [
                {"title": f"Result 1 for {query}", "snippet": "This is a simulated search result."},
                {"title": f"Result 2 for {query}", "snippet": "Another simulated search result."},
                {"title": f"Result 3 for {query}", "snippet": "Yet another simulated search result."}
            ]
            
            formatted_results = "\n\n".join([f"## {r['title']}\n{r['snippet']}" for r in results])
            
            if __event_emitter__:
                for r in results:
                    __event_emitter__({
                        "type": "citation",
                        "data": {
                            "content": r["snippet"],
                            "source": r["title"],
                            "metadata": {"type": "web_search", "query": query}
                        }})
            
            return formatted_results
        except Exception as e:
            return f"Error searching web: {str(e)}"
    
    def execute_shell(self, command: str, working_dir: str = "/home/user", __event_emitter__=None) -> str:
        """
        Execute a shell command.
        
        Args:
            command: Shell command to execute
            working_dir: Working directory for command execution
            
        Returns:
            Command output
        """
        if __event_emitter__:
            __event_emitter__({"type": "status", "data": {"text": f"Executing command: {command}"}})
        
        # This is a simulated shell execution
        # In a real implementation, you would use subprocess or similar
        return f"Simulated output of command: {command}\nExecuted in directory: {working_dir}"
    
    def browse_url(self, url: str, __event_emitter__=None) -> str:
        """
        Browse to a URL and extract content.
        
        Args:
            url: URL to browse
            
        Returns:
            Page content
        """
        if __event_emitter__:
            __event_emitter__({"type": "status", "data": {"text": f"Browsing URL: {url}"}})
        
        # This is a simulated browser operation
        # In a real implementation, you would use a browser automation library
        return f"Simulated content from URL: {url}\n\nThis would contain the extracted text from the webpage."
    
    def get_current_time(self) -> str:
        """
        Get the current date and time.
        
        Returns:
            Current date and time as text
        """
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_plan(self, task: str, __user__=None, __event_emitter__=None) -> str:
        """
        Generate a step-by-step plan for completing a task.
        
        Args:
            task: Description of the task to plan
            
        Returns:
            Step-by-step plan
        """
        if __event_emitter__:
            __event_emitter__({"type": "status", "data": {"text": f"Generating plan for: {task}"}})
        
        agent_name = "Manus"
        if __user__ and "valves" in __user__ and hasattr(__user__["valves"], "agent_name"):
            agent_name = __user__["valves"].agent_name
        
        steps = [
            f"1. Analyze the task: '{task}'",
            "2. Break down the task into manageable steps",
            "3. Execute each step methodically",
            "4. Verify results and make adjustments as needed",
            "5. Deliver final results to the user"
        ]
        
        return f"# {agent_name}'s Plan for: {task}\n\n" + "\n".join(steps)
    
    def summarize_text(self, text: str, max_length: int = 500) -> str:
        """
        Summarize a long text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary
            
        Returns:
            Summarized text
        """
        # This is a simulated text summarization
        # In a real implementation, you would use an NLP library or API
        words = text.split()
        if len(words) <= max_length / 5:  # Assuming average word length of 5
            return text
        
        return " ".join(words[:int(max_length / 5)]) + "... (summarized)"