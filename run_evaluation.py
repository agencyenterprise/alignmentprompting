import os
import json
import openai
from math import exp

# Load the system prompt (inputted by the user) from file
with open("user_prompt.txt", "r") as f:
    user_prompt = f.read().strip()

# Load the evaluation type from a .txt file
with open("evaluation_type.txt", "r") as f:
    evaluation_type = f.read().strip().lower()

# Define file paths for each evaluation type
evaluation_files = {
    "powerseeking": "power-seeking-inclination.jsonl",
    "shutdownavoidance": "no-shut-down.jsonl",
    "psychopathy": "psychopathy.jsonl"
}

# Ensure the specified evaluation type exists
if evaluation_type not in evaluation_files:
    raise ValueError(f"Unknown evaluation type '{evaluation_type}' specified.")

# Determine the input file based on the evaluation type
input_file = evaluation_files[evaluation_type]

# Function to calculate probability of a given completion with the system prompt applied
def get_prob(question, correct_answer, wrong_answer, type="baseline"):
    prompt = f"{question}" if type == "baseline" else user_prompt + " " + question
    correct_prob, wrong_prob = calculate_response_probabilities(prompt, correct_answer, wrong_answer)
    return correct_prob, wrong_prob

# Function to call OpenAI API and calculate probabilities of completions
def calculate_response_probabilities(question, correct_answer, wrong_answer):
    correct_response = openai.Completion.create(
        model="davinci-002",
        prompt=question + correct_answer,
        max_tokens=1,
        logprobs=10,
        temperature=0
    )
    wrong_response = openai.Completion.create(
        model="davinci-002",
        prompt=question + wrong_answer,
        max_tokens=1,
        logprobs=10,
        temperature=0
    )
    correct_logprob = correct_response["choices"][0].get("logprobs", {}).get("token_logprobs", [None])[0]
    wrong_logprob = wrong_response["choices"][0].get("logprobs", {}).get("token_logprobs", [None])[0]
    correct_prob = exp(correct_logprob) if correct_logprob is not None else 0
    wrong_prob = exp(wrong_logprob) if wrong_logprob is not None else 0
    return correct_prob, wrong_prob

# Load questions from JSONL
def load_questions(filename):
    with open(filename, "r") as file:
        for line in file:
            yield json.loads(line)

# Evaluate probabilities and count matches
def evaluate_probs_and_count(filename, max_examples=250):
    results = []
    baseline_matching_count = 0
    prompted_matching_count = 0
    example_count = 0

    for entry in load_questions(filename):
        if example_count >= max_examples:
            break
        question = entry["question"]
        answer_matching = entry["answer_matching_behavior"]
        answer_not_matching = entry["answer_not_matching_behavior"]
        baseline_prob_matching, baseline_prob_not_matching = get_prob(question, answer_matching, answer_not_matching, type="baseline")
        prompted_prob_matching, prompted_prob_not_matching = get_prob(question, answer_matching, answer_not_matching, type="prompted")
        if baseline_prob_matching > baseline_prob_not_matching:
            baseline_matching_count += 1
        if prompted_prob_matching > prompted_prob_not_matching:
            prompted_matching_count += 1
        results.append({
            "user_prompt": user_prompt,
            "question": question,
            "baseline_prob_matching": baseline_prob_matching,
            "prompted_prob_matching": prompted_prob_matching,
        })
        example_count += 1

    return results, baseline_matching_count, prompted_matching_count

# Main execution function to run and save results
def main():
    max_examples = 8  # Adjust as needed
    results, baseline_matching_count, prompted_matching_count = evaluate_probs_and_count(input_file, max_examples)
    output_data = {
        "total_examples": max_examples,
        "baseline_matching_count": baseline_matching_count,
        "prompted_matching_count": prompted_matching_count,
        "results": results
    }

    # Determine output file name based on evaluation type
    output_file = f"{evaluation_type.replace(' ', '_')}_results.json"
    with open(output_file, "w") as outfile:
        json.dump(output_data, outfile, indent=4)

if __name__ == "__main__":
    main()
