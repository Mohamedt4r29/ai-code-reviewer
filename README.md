\# AI-Powered Code Reviewer Tool



This project implements a CLI-based AI-powered code reviewer using the open-source \*\*Qwen2.5-Coder-7B-Instruct-Q8\_0\*\* model, running locally via `llama-cpp-python`. It analyzes Python and JavaScript code (extensible to other languages) and provides structured feedback on code quality, bugs, improvement suggestions, and security concerns. The tool outputs reviews in JSON, plain text, and colored CMD output for readability.



\## Features

\- \*\*LLM Integration\*\*: Uses Qwen2.5-Coder-7B-Instruct-Q8\_0 for local inference, no paid APIs.

\- \*\*Input\*\*: Reads code files from `./your\_codebase` (supports `.py`, `.js`, etc.), limited to 200 lines.

\- \*\*Output\*\*: Structured JSON and text files, plus colored CMD output with `colorama`.

\- \*\*Feedback\*\*:

&nbsp; - \*\*Bugs\*\*: Identifies errors (e.g., type coercion in JavaScript, TypeError in Python).

&nbsp; - \*\*Quality Issues\*\*: Flags style issues (e.g., unnecessary `return None`).

&nbsp; - \*\*Suggestions\*\*: Recommends modern features (e.g., f-strings, JSDoc).

&nbsp; - \*\*Security Concerns\*\*: Detects lack of input validation.

\- \*\*Caching\*\*: Stores LLM responses to avoid redundant processing.

\- \*\*Extensibility\*\*: Add new languages via `SUPPORTED\_EXTENSIONS` in the script.



\## Requirements

\- \*\*OS\*\*: Windows, macOS, or Linux

\- \*\*Python\*\*: 3.8+

\- \*\*RAM\*\*: 16GB+ (for Q8\_0 quantization)

\- \*\*Disk Space\*\*: ~5GB for model

\- \*\*Dependencies\*\*:

&nbsp; - `llama-cpp-python`

&nbsp; - `colorama`



\## Setup Instructions

1\. \*\*Clone the Repository\*\*:

&nbsp;  ```bash

&nbsp;  git clone https://github.com/Mohamedt4r29/ai-code-reviewer.git

&nbsp;  cd ai-code-reviewer

