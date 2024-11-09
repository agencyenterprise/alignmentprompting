import os
import json
import openai
from math import exp



# Load the system prompt (inputted by the user) from file
with open("user_prompt.txt", "r") as f:
    user_prompt = f.read().strip()  # Load and strip any extra whitespace

# Function to calculate probability of a given completion with the system prompt applied
def get_prob(question, correct_answer, wrong_answer, type="baseline"):
    # Construct the full prompt with the system prompt and question
    if(type=="baseline"):
        prompt = f"{question}"
    else:
        prompt = user_prompt + " " + question 
    
    # Calculate probabilities for the correct and wrong answers
    correct_prob, wrong_prob = calculate_response_probabilities(prompt, correct_answer, wrong_answer)
    
    return correct_prob, wrong_prob

# Function to call OpenAI API and calculate probabilities of completions
def calculate_response_probabilities(question, correct_answer, wrong_answer):
    # Get probability for the correct answer
    correct_response = openai.Completion.create(
        model="davinci-002",  # Adjust model as needed
        prompt=question+correct_answer,
        max_tokens=1,
        logprobs=10,  # Request log probabilities for the first token
        temperature=0
    )

    # Get probability for the wrong answer
    wrong_response = openai.Completion.create(
        model="davinci-002",
        prompt = question + wrong_answer,
        max_tokens=1,
        logprobs=10,
        temperature=0
    )

    # Extract log probability of the first token for correct and wrong answers using .get()
    correct_logprob = correct_response["choices"][0].get("logprobs", {}).get("token_logprobs", [None])[0]
    wrong_logprob = wrong_response["choices"][0].get("logprobs", {}).get("token_logprobs", [None])[0]

    # Calculate probability by exponentiating log probability
    correct_prob = exp(correct_logprob) if correct_logprob is not None else 0
    wrong_prob = exp(wrong_logprob) if wrong_logprob is not None else 0

    return correct_prob, wrong_prob

# Load the questions from JSONL
def load_questions(filename):
    with open(filename, "r") as file:
        for line in file:
            yield json.loads(line)

# Evaluate probabilities for the first 250 questions and count matches
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

        # Calculate probabilities with system prompt applied
        baseline_prob_matching, baseline_prob_not_matching = get_prob(question, answer_matching, answer_not_matching, type="baseline")
        
        prompted_prob_matching, prompted_prob_not_matching = get_prob(question, answer_matching, answer_not_matching, type="prompted")

        # Determine which answer has a higher probability
        if baseline_prob_matching > baseline_prob_not_matching:
            baseline_matching_count += 1
            
        if prompted_prob_matching > prompted_prob_not_matching:
            prompted_matching_count += 1


        results.append({
            "user_prompt": user_prompt,
            "question": question,
            "baseline_prob_matching": baseline_prob_matching,
            "prompted_prob_matching": baseline_prob_matching,
        })

        example_count += 1

    return results, baseline_matching_count, prompted_matching_count

# Main execution function to run and save results
def main():
    # Define input files and parameters
    power_file = "power-seeking-inclination.jsonl"  # Replace with your actual question data file
    shutdown_file = "no-shut-down.jsonl"
    psychopathy_file = "psychopathy.jsonl"
    
    max_examples = 5  # Adjust as needed

    # Run evaluation
    
    power_results, power_baseline_matching_count, power_prompted_matching_count = evaluate_probs_and_count(power_file, max_examples)

    shutdown_results, shutdown_baseline_matching_count, shutdown_prompted_matching_count = evaluate_probs_and_count(shutdown_file, max_examples)

    psychopathy_results, psychopathy_baseline_matching_count, psychopathy_prompted_matching_count = evaluate_probs_and_count(psychopathy_file, max_examples)
    
    # Save results to JSON
    power_output_data = {
        "total_examples": max_examples,
        "baseline_matching_count": power_baseline_matching_count,
        "prompted_matching_count": power_prompted_matching_count,
        "results": power_results
    }
    
    shutdown_output_data = {
        "total_examples": max_examples,
        "baseline_matching_count": shutdown_baseline_matching_count,
        "prompted_matching_count": shutdown_prompted_matching_count,
        "results": shutdown_results
    }
    
    psychopathy_output_data = {
        "total_examples": max_examples,
        "baseline_matching_count": psychopathy_baseline_matching_count,
        "prompted_matching_count": psychopathy_prompted_matching_count,
        "results": psychopathy_results
    }
    
    with open("power_results.json", "w") as outfile:
        json.dump(power_output_data, outfile, indent=4)
        
    with open("shutdown_results.json", "w") as outfile:
        json.dump(shutdown_output_data, outfile, indent=4)
    
    with open("psychopathy_results.json", "w") as outfile:
        json.dump(psychopathy_output_data, outfile, indent=4)

if __name__ == "__main__":
    main()