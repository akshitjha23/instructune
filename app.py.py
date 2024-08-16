import streamlit as st
import json
import logging
from openai import OpenAI

# Set up OpenAI client


# Configure logging
logging.basicConfig(filename='runtime.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_response(messages):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=1,
        max_tokens=2318,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={"type": "json_object"},
    )
    return completion.choices[0].message.content

def generate_prompt(system, history, user_input, err_output, eval_analysis, exp_output):
    messages = [
        {"role":"system", "content": "You are an auto prompt engineer. Your task is to evaluate the previous prompt, check for why the output was not in line with the instructions, and make small adjustments to the prompt. Think step by step.\n1. Evaluate why the output was not in line with the instructions.\n2. Check whether the previous prompt was clear and concise.\n3. Make small adjustments to the prompt to improve the output.\n4. Use the expected output to understand the regenration of the prompt.\n5. Return the new prompt.\n6. You must only regenerate the system prompt that has been passed to you.\n The other elements must only be used for analysis. I repeat, you must not regenerate elements like chat history, user_input, and assistant's response. Use the following JSON format: {\"analysis\":\"Your prompt analysis goes here in 40 words\",\"new_prompt\": \"new prompt here\"}"},
        {"role":"user", "content": f"Here's the previous system prompt and some additional context for your information:\nPrevious system prompt: {system}\n\n Chat History: {history}\nUser input: {user_input}\n Assistant's not in line output: {err_output}\nExpected output: {exp_output}\n Previous Analysis: {eval_analysis}"}
    ]
    return generate_response(messages)

def validate_prompt(eval_analysis, err_output, system, history, user_input, new_output, exp_output):
    messages = [
        {"role":"system", "content": "You are an auto prompt validator. Your task is to evaluate whether the output from the assistant based on the instructions is valid or not. Think step by step.\n1. Evaluate why the output was not in line with the instructions.\n Use the following JSON format: {\"analysis\":\"Your output analysis goes here in 40 words\",\"validation\": \"valid/invalid\"}"},
        {"role":"user", "content": f"Here's the system prompt and additional information to inform your analysis:\n System prompt: {system}\n\n Chat History: {history}\nUser input: {user_input}\n Assistant's output: {new_output}\nPrevious responses which were not in line with instructions: {err_output}\nExpected Output: {exp_output}\nPrevious analysis: {eval_analysis}"}
    ]
    return generate_response(messages)
st.sidebar.title("About This App")
api_key = st.sidebar.text_input("Please enter your OpenAI API key:")
cycles = st.sidebar.slider("Enter the number of cycles you want to run (maximum is 10):", min_value=1, max_value=10, value=2)
st.sidebar.markdown("""
This app uses OpenAI's GPT model to generate and validate prompts in a pipeline. Here is how it works:

1. **Input Fields**: You will enter the relevant information such as the system prompt, chat history, user input, error output, and expected output.
2. **Generate Prompt**: The app evaluates the provided input and generates a new prompt.
3. **Generate Response**: Using the new prompt, the app generates a response.
4. **Validate Response**: The app then validates the generated response to check if it meets the criteria.
5. **Iteration**: The app can iterate up to the number of cycles you specify in the sidebar to refine the prompt until a valid response is generated.
""")

st.title("Auto Prompt Engineering Pipeline")

st.subheader("System Prompt")
system = st.text_area(
    "Enter the system prompt content",
    height=200,
    help="Content for the system to understand the task. Example:\nYou are an AI assistant tasked with identifying the user's intent from given intent descriptions."
)

st.subheader("Chat History")
history_input = st.text_area(
    "Enter the history (in JSON format)",
    height=200,
    help='Enter the chat history between the assistant and user in JSON format. Example:\n[\n{"role": "assistant", "content": "Hi, how can I help you today?"},\n{"role": "user", "content": "Check bank balance"}\n{"role": "assistant", "content": "Here is your balance: 25$"}]'
)

history = json.loads(history_input) if history_input else []

st.subheader("User Input")
user_input = st.text_area(
    "Enter the user input content",
    height=50,
    help='Enter the latest user input. Example:\nAnd my credit card?'
)

st.subheader("Error Output")
err_output = st.text_area(
    "Enter the error output (in JSON format)",
    height=50,
    help='Enter the assistant\'s response that was not in line with the instructions in JSON format. Example:\n{"identified_intents":["apply for credit card"]}'
)

st.subheader("Expected Output")
exp_output = st.text_area(
    "Expected Output",
    height=50,
    help='Enter the expected correct output in JSON format. Example:\n{"identified_intents":[None]}'
)
client = OpenAI(api_key=api_key)
if st.button("Run Pipeline") and api_key != "":
    if not system.strip():
        st.error("System prompt content is required.")
    elif not history_input.strip():
        st.error("Chat history is required.")
    elif not user_input.strip():
        st.error("User input content is required.")
    elif not err_output.strip():
        st.error("Error output is required.")
    elif not exp_output.strip():
        st.error("Expected output is required.")
    else:
        with st.spinner("Running pipeline..."):
            try:
                # Log initial inputs
                logging.info("Initial System: %s", system)
                logging.info("History: %s", history)
                logging.info("User Input: %s", user_input)
                logging.info("Initial Error Output: %s", err_output)
                logging.info("Expected Output: %s", exp_output)

                # Pipeline execution with up to 5 cycles
                max_cycles = 2
                cycles = 0
                eval_analysis = None
                final_prompt = None
                while cycles < max_cycles:
                    cycles += 1
                    logging.info("Cycle %d: Starting", cycles)
                    logging.info("Cycle %d: System: %s", cycles, system)
                    logging.info("Cycle %d: Error Output: %s", cycles, err_output)
                    logging.info("Cycle %d: Evaluation Analysis: %s", cycles, eval_analysis)
                    
                    #Generate the new prompt
                    new_prompt_response = generate_prompt(system, history, user_input, err_output, eval_analysis, exp_output)
                    new_prompt = json.loads(new_prompt_response)["new_prompt"]
                    logging.info("Cycle %d: New Prompt: %s", cycles, new_prompt)
                    
                    # Create new message set based on the new prompt
                    new_messages = [{"role": "system", "content": new_prompt}] + history + [{"role": "user", "content": user_input}]
                    
                    # Generate response for the new prompt
                    new_response = generate_response(new_messages)
                    logging.info("Cycle %d: New Response: %s", cycles, new_response)

                    # Validate the response
                    evaluation_response = validate_prompt(eval_analysis, err_output, new_prompt, history, user_input, new_response, exp_output)
                    evaluation = json.loads(evaluation_response)
                    eval_analysis = evaluation["analysis"]
                    logging.info("Cycle %d: Evaluation: %s", cycles, evaluation)

                    if evaluation["validation"] == "valid":
                        logging.info("Cycle %d: Final Valid Prompt: %s", cycles, new_prompt)
                        final_prompt = new_prompt
                        break
                    else:
                        # Update system and err_output for the next iteration
                        err_output = new_response  # The new response becomes the err_output for the next iteration
                        system = new_prompt  # Use the new prompt as the starting system prompt

                # Log final prompt whether valid or after max cycles
                if final_prompt is None:
                    final_prompt = new_prompt
                    logging.info("Max cycles reached. Final Prompt: %s", new_prompt)
                    st.text("Max cycles reached")
                else:
                    logging.info("Final Valid Prompt after %d cycles: %s", cycles, final_prompt)

                # Display the final prompt in Streamlit
                st.subheader("Final Prompt")
                st.text_area("Final Prompt", final_prompt, height=200)

            except Exception as e:
                st.error(f"An error occurred: {e}")
                logging.error("An error occurred: %s", e)
else:
    st.info("Please enter your OpenAI API key in the sidebar.")