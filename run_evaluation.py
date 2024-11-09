import os
import json
import openai
from math import exp

# Load your OpenAI API key
openai.api_key = os.getenv("k-proj-JayVkRXLjI0PSWXs6aB6XDzPIQ15JhjAsTKuXJgRvaU6tVf__AtUKWSW3wPrMeOoyVxdshz-91T3BlbkFJWMm8OqxxQwX6i0zRNPgPFXYBfIXKvg8QSYb0DuFFtKDasDSo_BW4RICWQhZ_gcU5OekEyVPjQA")

# Load god_prompt from file
with open("god_prompt.txt", "r") as f:
    god_prompt = f.read().strip()  # Load and strip any extra whitespace

# Function to calculate probability of a given completion with chat template applied
def get_prob(question, correct_answer, wrong_answer, yeshua, test):
    # Apply chat template with conversation structure, using god_prompt if yeshua is True
    if yeshua:
        if test == "attention":
            prompt_content = question + " " + god_prompt + " " + question
        else:
            prompt_content = god_prompt + " " + question
    else:
        prompt_content = question

    # Generate the prompt for the OpenAI API with the specified structure
    messages = [{"role": "system", "content": prompt_content}, {"role": "user", "content": question}]
    
    # Call OpenAI API to get probabilities
    correct_prob, wrong_prob = calculate_response_probabilities(messages, correct_answer, wrong_answer)
    
    return correct_prob, wrong_prob

# Function to call OpenAI API and calculate probabilities of completions
def calculate_response_probabilities(messages, correct_answer, wrong_answer):
    correct_prompt = messages + [{"role": "assistant", "content": correct_answer}]
    wrong_prompt = messages + [{"role": "assistant", "content": wrong_answer}]
    
    correct_response = openai.ChatCompletion.create(
        model="gpt-4",  # Use "gpt-4" or any other appropriate OpenAI model
        messages=correct_prompt,
        logprobs=10,  # Get token-level log probabilities
        max_tokens=0,  # We are only interested in probabilities of the prompt
    )

    wrong_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=wrong_prompt,
        logprobs=10,
        max_tokens=0,
    )
    
    # Extract logprobs for the last token for each response
    correct_logprobs = correct_response['choices'][0]['logprobs']['token_logprobs']
    wrong_logprobs = wrong_response['choices'][0]['logprobs']['token_logprobs']

    # Calculate total probability by exponentiating and summing logprobs
    correct_prob = sum(exp(logprob) for logprob in correct_logprobs)
    wrong_prob = sum(exp(logprob) for logprob in wrong_logprobs)

    return correct_prob, wrong_prob

# Load the questions from JSONL
def load_questions(filename):
    with open(filename, "r") as file:
        for line in file:
            yield json.loads(line)

# Evaluate probabilities for the first 250 questions and count matches
def evaluate_probs_and_count(filename, max_examples=250, yeshua=False, test=None):
    results = []
    matching_count = 0
    not_matching_count = 0
    example_count = 0

    for entry in load_questions(filename):
        if example_count >= max_examples:
            break

        question = entry["question"]
        answer_matching = entry["answer_matching_behavior"]
        answer_not_matching = entry["answer_not_matching_behavior"]

        # Calculate probabilities with chat template applied
        prob_matching, prob_not_matching = get_prob(question, answer_matching, answer_not_matching, yeshua, test)

        # Determine which answer has a higher probability
        if prob_matching > prob_not_matching:
            matching_count += 1
        else:
            not_matching_count += 1

        results.append({
            "question": question,
            "prob_matching": prob_matching,
            "prob_not_matching": prob_not_matching,
        })

        example_count += 1

    return results, matching_count, not_matching_count

# Main execution function to run and save results
def main():
    # Define input files and parameters
    input_file = "questions.jsonl"  # Replace with your actual question data file
    max_examples = 250  # Adjust as needed
    yeshua = True  # Set to True to use god_prompt
    test_mode = "attention"  # Can be adjusted as needed

    # Run evaluation
    results, matching_count, not_matching_count = evaluate_probs_and_count(input_file, max_examples, yeshua, test_mode)

    # Print results summary
    print(f"Total Examples Evaluated: {max_examples}")
    print(f"Matching Count: {matching_count}")
    print(f"Not Matching Count: {not_matching_count}")

    # Save results to JSON
    output_data = {
        "total_examples": max_examples,
        "matching_count": matching_count,
        "not_matching_count": not_matching_count,
        "results": results
    }
    with open("evaluation_results.json", "w") as outfile:
        json.dump(output_data, outfile, indent=4)

if __name__ == "__main__":
    main()
