
```markdown
# AI-Powered Code Reviewer Tool

This project implements a CLI-based AI-powered code reviewer using the open-source **Qwen2.5-Coder-7B-Instruct-Q8_0** model, running locally via `llama-cpp-python`. It analyzes Python and JavaScript code (extensible to other languages) and provides structured feedback on code quality, bugs, improvement suggestions, and security concerns. The tool outputs reviews in JSON, plain text, and colored CMD output for readability.

## Features
- **LLM Integration**: Uses Qwen2.5-Coder-7B-Instruct-Q8_0 for local inference, no paid APIs.
- **Input**: Reads code files from `./your_codebase` (supports `.py`, `.js`, etc.), limited to 200 lines.
- **Output**: Structured JSON and text files, plus colored CMD output with `colorama`.
- **Feedback**:
  - **Bugs**: Identifies errors (e.g., type coercion in JavaScript, TypeError in Python).
  - **Quality Issues**: Flags style issues (e.g., unnecessary `return None`).
  - **Suggestions**: Recommends modern features (e.g., f-strings, JSDoc).
  - **Security Concerns**: Detects lack of input validation.
- **Caching**: Stores LLM responses to avoid redundant processing.
- **Extensibility**: Add new languages via `SUPPORTED_EXTENSIONS` in the script.

## Requirements
- **OS**: Windows, macOS, or Linux
- **Python**: 3.8+
- **RAM**: 16GB+ (for Q8_0 quantization)
- **Disk Space**: ~5GB for model
- **Dependencies**:
  - `llama-cpp-python`
  - `colorama`

## Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Mohamedt4r29/ai-code-reviewer.git
   cd ai-code-reviewer
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install llama-cpp-python colorama
   ```

4. **Download the Model**:
   - Download **Qwen2.5-Coder-7B-Instruct-Q8_0** from Hugging Face:
     - URL: `https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`
     - File: `qwen2.5-coder-7b-instruct-q8_0.gguf`
   - Place the `.gguf` file in `./models/`:
     ```bash
     mkdir models
     mv /path/to/qwen2.5-coder-7b-instruct-q8_0.gguf models/
     ```

5. **Prepare Codebase**:
   - Place code files in `./your_codebase/` (e.g., `app.js`, `example.py`).
   - Example files are included in the repository.

## Usage
1. **Run the Tool**:
   ```bash
   python local_code_reviewer.py
   ```
   - Processes all files in `./your_codebase` with supported extensions (`.py`, `.js`, etc.).
   - Outputs:
     - JSON reviews: `./code_reviews/<filename>_review.json`
     - Text reviews: `./code_reviews/<filename>_review.txt`
     - Colored CMD output for immediate feedback (bugs in red, quality issues in yellow, suggestions in green, security concerns in magenta).

2. **Sample Input** (`your_codebase/example.py`):
   ```python
   def greet(name):
       """Greet a user by name."""
       print("Hello, " + name)
       return None
   
   greet("World")
   ```

3. **Sample Output** (`code_reviews/example_review.txt`):
   ```
   === Code Review for example.py ===
   
   --------------------------------------------------------------------------------
   
   Bugs:
   
     Line 3:
       Code       : print("Hello, " + name)
       Description: Potential TypeError if 'name' is not a string (e.g., None)
   
   Quality Issues:
   
     Line 4:
       Code       : return None
       Description: Unnecessary 'return None' as Python functions implicitly return None
   
   Suggestions:
   
     Line 3:
       Code       : print("Hello, " + name)
       Fix        : print(f'Hello, {name}')
       Description: Use f-string for better readability and performance
   
     Line 1:
       Code       : def greet(name):
       Fix        : def greet(name: str) -> None:
       Description: Add type hints for clarity and IDE support
   
   Security Concerns:
   
     Line 3:
       Code       : print("Hello, " + name)
       Description: Lack of input validation could raise TypeError for non-string inputs
   
   ================================================================================
   ```

4. **Sample Input** (`your_codebase/app.js`):
   ```javascript
   function greet(name) {
       // Greet a user by name
       console.log("Hello, " + name);
       return null;
   }
   greet("World");
   ```

5. **Sample Output** (`code_reviews/app_review.txt`):
   ```
   === Code Review for app.js ===
   
   --------------------------------------------------------------------------------
   
   Bugs:
   
     Line 2:
       Code       : console.log("Hello, " + name);
       Description: Potential type coercion if 'name' is null or undefined
   
   Quality Issues:
   
     Line 4:
       Code       : return null;
       Description: Unnecessary 'return null' as the function's purpose is logging
   
   Suggestions:
   
     Line 2:
       Code       : console.log("Hello, " + name);
       Fix        : console.log(`Hello, ${name}`);
       Description: Use template literals for better readability and modern JavaScript
   
     Line 1:
       Code       : function greet(name) {
       Fix        : /** Greet a user by name */
       function greet(name) {
       Description: Add JSDoc for better documentation and IDE support
   
   Security Concerns:
   
     Line 2:
       Code       : console.log("Hello, " + name);
       Description: Lack of input validation could lead to unexpected output for null/undefined inputs
   
   ================================================================================
   ```

## Write-Up
### LLM Choice
- **Model**: Qwen2.5-Coder-7B-Instruct-Q8_0
- **Why**:
  - Optimized for code-related tasks, outperforming general-purpose models like Mistral-7B for code review.
  - Q8_0 quantization balances performance and resource usage (runs on 16GB RAM, CPU-only).
  - Available on Hugging Face, compatible with `llama-cpp-python` for local inference.
- **Setup**: Downloaded GGUF file from Hugging Face, ensuring no internet access is needed during inference.

### Limitations
- **Context Length**: Limited to 2048 tokens, mitigated by truncating input to 200 lines.
- **False Positives**: LLM may overflag issues; JSON cleaning reduces errors.
- **Language Support**: Supports Python and JavaScript; other languages need prompt tuning.
- **Caching**: Basic file-based caching implemented, but no advanced cache management.

### Future Improvements
- **Web Interface**: Add Flask or FastAPI UI for file uploads and interactive reviews.
- **Extended Languages**: Support C++, Java, etc., with tailored prompts.
- **Custom Rules**: Allow users to define coding standards (e.g., PEP8, ESLint).
- **Advanced Caching**: Use a database or LRU cache for faster lookups.

## Sample Files
- **Python**: `your_codebase/example.py` (simple function with string concatenation).
- **JavaScript**: `your_codebase/app.js` (similar function with console logging).

## Contributing
- Fork the repository, make changes, and submit a pull request.
- Issues and feature requests are welcome!

## License
MIT License
```



### Notes
- **Content**: The `README.md` includes:
  - Setup instructions (clone, virtual environment, dependencies, model download).
  - Usage guide with sample inputs (`app.js`, `example.py`) and outputs (text files).
  - Write-up covering LLM choice, limitations, and future improvements.
  - Sample files and license details.
- **Task Compliance**: Matches the task’s requirements for a public GitHub repo, clear `README.md`, sample input/output, and write-up.
- **Previous Context**: Assumes `local_code_reviewer.py` includes line limit (200 lines) and caching (from previous response), and `your_codebase/` contains `app.js` and `example.py`.

If you need help with the `LICENSE` file, additional samples (e.g., C++), or a web interface, let me know!
