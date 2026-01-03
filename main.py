import sys
import os
import argparse

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import agent_loop

def main():
    parser = argparse.ArgumentParser(description="Stickman Video Generation Agent")
    parser.add_argument("prompt", nargs="?", help="The animation prompt (e.g., 'Make a stickman jump')", default="Make a stickman waving his hand")
    parser.add_argument("--model", help="Ollama model to use", default="deepseek-r1:14b")
    
    args = parser.parse_args()
    
    print("Welcome to the Zero-Cost Stickman Agent.")
    print(f"Goal: {args.prompt}")
    print(f"Model: {args.model}")
    print("------------------------------------------")
    
    agent_loop(args.prompt, model=args.model)

if __name__ == "__main__":
    main()
