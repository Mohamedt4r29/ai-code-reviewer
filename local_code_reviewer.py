import os
from pathlib import Path
from llama_cpp import Llama
import json
import re
import logging

# Configure logging
logging.basicConfig(
    filename="code_reviewer.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
CODEBASE_DIR = "./your_codebase"
OUTPUT_DIR = "./code_reviews"
MODEL_PATH = "./models/qwen2.5-coder-7b-instruct-q8_0.gguf"
SUPPORTED_EXTENSIONS = {".py", ".js", ".cpp", ".java", ".ts", ".html", ".css", ".go"}

# Initialize the LLM with GPU support
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    n_threads=8,
    n_gpu_layers=10,  # Offload 10 layers to GPU (adjust if VRAM error)
    verbose=False
)

def read_code_file(file_path):
    """Read content of a code file, splitting into chunks if necessary."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if len(content) > 3000:
                logging.info(f"Chunking file {file_path} due to large size")
                return [content[i:i+3000] for i in range(0, len(content), 3000)]
            return content
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        return f"Error reading file: {str(e)}"

def clean_json_string(text):
    """Attempt to clean and extract valid JSON from LLM output."""
    text = text.strip()
    # Remove BOM and non-printable characters
    text = text.encode('utf-8').decode('utf-8-sig')
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
    # Extract JSON from ```json ``` markers or raw JSON
    json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```|\{[\s\S]*?\}', text, re.DOTALL)
    if not json_match:
        logging.error(f"No valid JSON found in LLM output: {text}")
        return json.dumps({
            "error": "No valid JSON found in output",
            "raw_output": text
        }, indent=2)
    
    json_str = json_match.group(1) or json_match.group(0)
    # Replace single quotes with double quotes
    json_str = json_str.replace("'", '"')
    # Remove trailing commas
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    json_str = re.sub(r',\s*(?=\n\s*[}\]])', '', json_str)
    json_str = re.sub(r',,+', ',', json_str)
    # Truncate at last valid closing brace
    last_brace = json_str.rfind('}')
    if last_brace != -1:
        json_str = json_str[:last_brace+1]
    # Log raw and cleaned JSON
    logging.info(f"Raw LLM output: {text}")
    logging.info(f"Cleaned JSON string: {json_str}")
    try:
        json_dict = json.loads(json_str)
        return json.dumps(json_dict, indent=2)
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing failed: {str(e)} at line {e.lineno}, column {e.colno}")
        # Fallback: reconstruct minimal valid JSON
        fallback_json = {
            "bugs": [],
            "quality_issues": [],
            "suggestions": [],
            "security_concerns": []
        }
        logging.info(f"Fallback JSON used for {json_str}")
        return json.dumps(fallback_json, indent=2)

def filter_invalid_suggestions(review_json, file_name):
    """Filter out invalid suggestions or quality issues."""
    try:
        review = json.loads(review_json)
        if "error" in review:
            return review_json
        
        # Filter quality_issues and suggestions
        for key in ["quality_issues", "suggestions"]:
            filtered = []
            for item in review[key]:
                code = item.get("code", "").strip()
                description = item.get("description", "").lower()
                # Skip if code is a comment/docstring or description mentions comments
                if not (code.startswith("//") or code.startswith("/*") or code.startswith('"""') or code.startswith("'''") or "comment" in description):
                    filtered.append(item)
                else:
                    logging.info(f"Filtered out {key} item for {file_name}: {code}")
            review[key] = filtered
        return json.dumps(review, indent=2)
    except json.JSONDecodeError:
        return review_json

def format_review_for_display(review_json, file_name):
    """Format the review JSON for human-readable CMD and text file output."""
    try:
        review = json.loads(review_json)
        if "error" in review:
            return f"\n=== Error Reviewing {file_name} ===\n\nError: {review['error']}\n\nRaw Output:\n{review['raw_output']}\n\n{'=' * 80}\n"
        
        output = f"\n=== Code Review for {file_name} ===\n\n{'-' * 80}\n"
        
        output += "Bugs:\n"
        if review["bugs"]:
            for bug in review["bugs"]:
                output += f"\n  Line {bug['line']}:\n"
                output += f"    Code       : {bug['code']}\n"
                output += f"    Description: {bug['description']}\n"
        else:
            output += "\n  None\n"
        
        output += "\nQuality Issues:\n"
        if review["quality_issues"]:
            for issue in review["quality_issues"]:
                output += f"\n  Line {issue['line']}:\n"
                output += f"    Code       : {issue['code']}\n"
                output += f"    Description: {issue['description']}\n"
        else:
            output += "\n  None\n"
        
        output += "\nSuggestions:\n"
        if review["suggestions"]:
            for suggestion in review["suggestions"]:
                output += f"\n  Line {suggestion['line']}:\n"
                output += f"    Code       : {suggestion['code']}\n"
                output += f"    Fix        : {suggestion['fix']}\n"
                output += f"    Description: {suggestion['description']}\n"
        else:
            output += "\n  None\n"
        
        output += "\nSecurity Concerns:\n"
        if review["security_concerns"]:
            for concern in review["security_concerns"]:
                output += f"\n  Line {concern['line']}:\n"
                output += f"    Code       : {concern['code']}\n"
                output += f"    Description: {concern['description']}\n"
        else:
            output += "\n  None\n"
        
        output += f"\n{'=' * 80}\n"
        return output
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format for review of {file_name}")
        return f"\n=== Error Formatting Review for {file_name} ===\n\nError: Invalid JSON\n\n{'=' * 80}\n"

def save_review(file_name, review):
    """Save the review to a JSON file and a human-readable text file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_stem = Path(file_name).stem
    json_path = os.path.join(OUTPUT_DIR, f"{file_stem}_review.json")
    txt_path = os.path.join(OUTPUT_DIR, f"{file_stem}_review.txt")
    
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(review)
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(format_review_for_display(review, file_name))
    logging.info(f"Review saved for {file_name} at {json_path} and {txt_path}")

def generate_review(code, file_name):
    """Generate a code review using the LLM."""
    ext = Path(file_name).suffix.lower()
    lang_map = {
        ".py": "Python", 
        ".js": "JavaScript", 
        ".cpp": "C++", 
        ".java": "Java", 
        ".ts": "TypeScript",
        ".html": "HTML",
        ".css": "CSS",
        ".go": "Go"
    }
    language = lang_map.get(ext, "Unknown")

    if isinstance(code, list):
        reviews = []
        for i, chunk in enumerate(code):
            review = generate_review_chunk(chunk, file_name, language, i)
            reviews.append(review)
        try:
            aggregated = {"bugs": [], "quality_issues": [], "suggestions": [], "security_concerns": []}
            for review in reviews:
                review_dict = json.loads(review)
                for key in aggregated:
                    aggregated[key].extend(review_dict.get(key, []))
            return filter_invalid_suggestions(json.dumps(aggregated, indent=2), file_name)
        except json.JSONDecodeError:
            logging.error(f"Failed to aggregate chunked reviews for {file_name}")
            return json.dumps({"error": "Failed to aggregate chunked reviews", "raw_outputs": reviews}, indent=2)
    
    return filter_invalid_suggestions(generate_review_chunk(code, file_name, language, 0), file_name)

def generate_review_chunk(code, file_name, language, chunk_index):
    """Generate a review for a single code chunk."""
    prompt = f"""
You are an expert code reviewer for {language} code. Review the following code from file '{file_name}' (chunk {chunk_index}) and provide a structured review in **valid JSON format** (use double quotes, no trailing commas). Include exactly these keys:
- "bugs": Array of potential bugs or errors (up to 5, e.g., type errors, null/undefined handling). Each entry must have "line" (line number, 1-based), "code" (exact code snippet), and "description" (issue explanation).
- "quality_issues": Array of code quality issues (up to 5, e.g., readability, structure). Each entry must have "line" (line number, 1-based), "code" (exact code snippet), and "description" (issue explanation). Do not overlap with bugs.
- "suggestions": Array of actionable improvements (up to 5, e.g., f-strings for Python, template literals/JSDoc for JavaScript, type hints for Python). Each entry must have "line" (line number, 1-based), "code" (exact code snippet), "fix" (example fix), and "description" (why the fix is better).
- "security_concerns": Array of security concerns (up to 5, e.g., input validation issues). Each entry must have "line" (line number, 1-based), "code" (exact code snippet), and "description" (issue explanation).

Rules:
- **Do not suggest adding, removing, or modifying comments or docstrings unless they are factually incorrect or misleading** (e.g., a comment that incorrectly describes the code's behavior).
- Avoid suggesting renaming functions unless the name is misleading (e.g., 'greet' is clear for a greeting function).
- Use modern language features (e.g., f-strings for Python, template literals for JavaScript, type hints for Python, JSDoc for JavaScript).
- For JavaScript, always suggest template literals for string concatenation (e.g., console.log).
- For Python, suggest removing explicit 'return None' when unnecessary, as functions return None by default.
- Include input validation suggestions where applicable (e.g., check for undefined/null in JavaScript, type checking in Python).
- For JavaScript, note that console.log returns undefined, not the logged string.
- Ensure issues do not overlap across categories (e.g., a bug should not also appear as a quality issue).
- Ensure accurate line numbers (1-based) and exact code snippets.
- Return empty arrays if no issues are found.
- Ensure valid JSON with no trailing commas, hidden characters, or syntax errors.

Code:
```
{code}
```
Return the JSON object enclosed in ```json ``` markers.
"""
    try:
        response = llm(
            prompt,
            max_tokens=1024,
            temperature=0.3,
            stop=["</s>"]
        )
        raw_output = response["choices"][0]["text"]
        cleaned_output = clean_json_string(raw_output)
        try:
            json.loads(cleaned_output)
            return cleaned_output
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON after cleaning for {file_name}, chunk {chunk_index}")
            return json.dumps({
                "error": "LLM produced invalid JSON",
                "raw_output": raw_output
            }, indent=2)
    except Exception as e:
        logging.error(f"LLM inference failed for {file_name}, chunk {chunk_index}: {str(e)}")
        return json.dumps({"error": f"LLM inference failed: {str(e)}"}, indent=2)

def main():
    """Process all code files in the codebase directory."""
    logging.info("Starting code review process")
    if not os.path.exists(CODEBASE_DIR):
        logging.error(f"Codebase directory {CODEBASE_DIR} does not exist")
        print(f"Codebase directory {CODEBASE_DIR} does not exist")
        return

    for root, _, files in os.walk(CODEBASE_DIR):
        for file in files:
            if Path(file).suffix in SUPPORTED_EXTENSIONS:
                file_path = os.path.join(root, file)
                logging.info(f"Reviewing {file_path}")
                print(f"Reviewing {file_path}...")
                code = read_code_file(file_path)
                if isinstance(code, str) and "Error" in code:
                    print(code)
                    logging.error(code)
                    continue
                review = generate_review(code, file)
                try:
                    json.loads(review)
                    save_review(file, review)
                    print(format_review_for_display(review, file))
                    print(f"Review saved for {file}")
                except json.JSONDecodeError:
                    logging.error(f"Invalid review format for {file}")
                    print(f"Invalid review format for {file}")
                    save_review(file, json.dumps({"error": "Invalid LLM response format after cleaning"}, indent=2))
                    print(format_review_for_display(review, file))
                    print(f"Fallback review saved for {file}")

if __name__ == "__main__":
    main()