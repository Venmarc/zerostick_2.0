import ollama
import subprocess
import json
import re
import os

# ------------------------------------------------------------------------------
# A.1 The System Prompt
# ------------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an autonomous Python Animation Agent specialized in procedural stick figure animation.
CORE OBJECTIVE: Translate natural language prompts into complete, executable Python scripts that generate MP4 videos using OpenCV.
TOOLS & LIBRARIES:
1. OpenCV (cv2): Use for all rendering.
    o Canvas: np.zeros((H, W, 3), np.uint8)
    o Drawing: cv2.line, cv2.circle
    o Colors: (B, G, R) tuples.
    o Anti-aliasing: Always use cv2.LINE_AA.
2. Math: Use math.sin, math.cos for periodic motion.
3. Numpy: Use for vector operations.
CONSTRAINTS:
    - Do NOT use external assets (images/sprites). Draw everything via code.
    - OUTPUT FORMAT: You must provide a valid JSON object with keys:
        o "thought": Your reasoning about the physics/math.
        o "code": The complete Python script.
    - COORDINATE SYSTEM: Remember OpenCV (0,0) is TOP-LEFT. Y increases DOWNWARDS.
ERROR HANDLING: If your code fails, analyze the error provided in the user prompt and generate a FIXED version."""

# ------------------------------------------------------------------------------
# A.2 Python Orchestrator Script
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# A.2 Python Orchestrator Script
# ------------------------------------------------------------------------------

def run_python_code(code, working_dir="."):
    filename = os.path.join(working_dir, "agent_script.py")
    
    # Write the generated code to a file
    with open(filename, "w") as f:
        f.write(code)
    
    # Run with timeout to prevent infinite loops
    try:
        # We run in the working_dir so it generates output files there
        result = subprocess.run(
            ["python3", "agent_script.py"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", "Error: Code execution timed out after 60 seconds."
    except Exception as e:
        return "", f"Error: {str(e)}"

def extract_json(content):
    # Regex to find JSON block
    # We look for the first JSON object structure
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            # Fallback: sometimes LLMs produce broken JSON, we'll try to just find the code block if JSON fails
            pass
    
    # Fallback to finding code block if JSON parsing fails but code ticks exist
    code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
    if code_match:
        return {"thought": "Extraction Fallback", "code": code_match.group(1).strip()}
        
    return None

def agent_loop(user_request, model='deepseek-r1-distill-qwen-14b', callback=None):
    """
    Main agent loop.
    callback: function(type: str, content: str) -> None
    types: 'status', 'log', 'error', 'video'
    """
    
    def log(type_, content):
        if callback:
            callback(type_, content)
        else:
            print(f"[{type_.upper()}] {content}")

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_request}
    ]

    max_turns = 5
    log('status', f"Starting Agent Loop for request: '{user_request}'")

    for turn in range(max_turns):
        log('log', f"--- Turn {turn + 1} ---")

        # 1. Inference
        log('status', "Thinking...")
        try:
            response = ollama.chat(model=model, messages=messages)
        except Exception as e:
            log('error', f"Error communicating with Ollama: {e}")
            return

        assistant_msg = response['message']['content']
        messages.append({'role': 'assistant', 'content': assistant_msg})

        # 2. Parse
        data = extract_json(assistant_msg)
        if not data or 'code' not in data:
            log('log', "No code generated. Ending or asking for clarification.")
            break

        code = data['code']
        thought = data.get('thought', 'No thought provided')
        log('log', f"Thought: {thought}")

        # 3. Execute
        log('status', "Executing code...")
        stdout, stderr = run_python_code(code, working_dir=os.getcwd())

        # 4. Feedback
        if stderr:
            log('error', f"Error Detected: {stderr}")
            feedback = f"Your code failed with this error:\n{stderr}\nPlease fix it."
            messages.append({'role': 'user', 'content': feedback})
        else:
            log('status', "Execution Successful.")
            if stdout:
                log('log', f"Output: {stdout}")
            
            # Check for generated video files
            # The agent typically names them or we can just look for the most recent mp4
            # For now, let's assume if it succeeds, we look for any .mp4 file created in the last few seconds
            # Or we just return success.
            # Ideally the agent should tell us the filename, but the current prompt doesn't strictly enforce outputting the filename in JSON.
            # We will rely on listing the directory in the server or checking known output names.
            
            break 

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = "Create a video of a stickman waving his hand."
    
    agent_loop(prompt)

