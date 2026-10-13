import os
import google.generativeai as genai


def main():
    """
    Main function to run the Gemini API chatbot.
    """
    # Get the API key from an environment variable.
    # It's a best practice to keep API keys out of your code.
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please set your API key and try again.")
        return

    # Configure the API key for the generative AI library.
    genai.configure(api_key=api_key)

    # Instantiate the model. We'll use the 'gemini-pro' model for text generation.
    try:
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"Error initializing model: {e}")
        return

    print("Gemini API Chatbot")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("-" * 30)

    # Start a loop to interact with the user.
    while True:
        try:
            user_prompt = input("You: ")

            # Check for exit commands
            if user_prompt.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break

            # Send the prompt to the model and get a response.
            response = model.generate_content(user_prompt)

            # Print the model's response.
            print(f"Gemini: {response.text}")

        except Exception as e:
            print(f"An error occurred: {e}")
            continue


if __name__ == "__main__":
    main()
