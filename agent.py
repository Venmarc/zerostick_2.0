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

def run_python_code(code, working_dir="."):
    filename = os.path.join(working_dir, "agent_script.py")
    
    # Write the generated code to a file
    with open(filename, "w") as f:
        f.write(code)
    
    print(f" -> Code saved to {filename}")

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

def agent_loop(user_request, model='deepseek-r1-distill-qwen-14b'):
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_request}
    ]

    max_turns = 5
    print(f"Starting Agent Loop for request: '{user_request}'")

    for turn in range(max_turns):
        print(f"\n--- Turn {turn + 1} ---")

        # 1. Inference
        print(" -> Thinking...")
        try:
            response = ollama.chat(model=model, messages=messages)
        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            return

        assistant_msg = response['message']['content']
        # print(f"Agent Thought: {assistant_msg[:200]}...") # Optional: print snippet
        messages.append({'role': 'assistant', 'content': assistant_msg})

        # 2. Parse
        data = extract_json(assistant_msg)
        if not data or 'code' not in data:
            print(" -> No code generated. Ending or asking for clarification.")
            # If no code, maybe it's just talking. Let's see if we should continue or break.
            # Ideally we check if it says "FINAL ANSWER" or similar, but for now we break if no code.
            break

        code = data['code']
        thought = data.get('thought', 'No thought provided')
        print(f" -> Thought: {thought}")

        # 3. Execute
        print(" -> Executing code...")
        stdout, stderr = run_python_code(code, working_dir=os.getcwd())

        # 4. Feedback
        if stderr:
            print(f" -> Error Detected: {stderr}")
            feedback = f"Your code failed with this error:\n{stderr}\nPlease fix it."
            messages.append({'role': 'user', 'content': feedback})
        else:
            print(" -> Execution Successful.")
            if stdout:
                print(f" -> Output: {stdout}")
            # If successful, we ask for a check or simply break? 
            # The prompt implies we stop on success or maybe verify. 
            # For now, let's assume success means done.
            break 

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = "Create a video of a stickman waving his hand."
    
    agent_loop(prompt)
