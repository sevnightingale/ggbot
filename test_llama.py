# test_llama.py
import sys
from llama_cpp import Llama

# Path to your quantized GGUF model
MODEL_PATH = "/root/ggbot/models/tinyllama-quantized.gguf"

def test_llama_model():
    try:
        # Load the model
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,
            n_threads=1,  # Matches your 1 vCPU VM
            verbose=True  # Shows loading details
        )
        print("Model loaded successfully!")

        # Define a test prompt with clear instruction
        prompt = "Provide steps to log into a website with username 'user123' and password 'pass456'."

        # Generate output
        result = llm(
            prompt,
            max_tokens=100,
            temperature=0.7,  # Balanced randomness
            stop=["</s>"],    # Explicitly stop at end-of-sequence token
            echo=False        # Don’t repeat the prompt in the output
        )

        # Print results
        generated_text = result["choices"][0]["text"]
        print(f"Prompt: {prompt}")
        print(f"Generated Output: {generated_text}")
        print(f"Token Count: {result['usage']['completion_tokens']}")

    except FileNotFoundError:
        print(f"Error: Model file not found at {MODEL_PATH}. Please check the path.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading or running the model: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_llama_model()