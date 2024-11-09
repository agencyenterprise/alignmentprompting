import streamlit as st
import subprocess
import json

# Step 1: Title and instructions
st.title("Prompt Alignment Evaluation Tool")
st.write("Introduce a prompt you think would make the AI more aligned with humans. We'll use it as a system prompt and evaluate the AI's performance.")
# Step 2: User input for the system prompt
user_prompt = st.text_area("Enter your alignment system prompt here:", height=200)

# Step 3: Submit button
if st.button("Run Evaluation"):
    # Step 4: Save the prompt as a system prompt
    with open("system_prompt.txt", "w") as f:
        f.write(user_prompt)
    
    # Step 5: Run the evaluation script
    st.write("Running evaluation with your custom system prompt...")
    result = subprocess.run(["python", "run_evaluation.py", "--system_prompt", "system_prompt.txt"], capture_output=True, text=True)

    # Step 6: Parse the results and visualize
    if result.returncode == 0:
        st.success("Evaluation completed successfully.")
        
        # Load results from output JSON or capture
        evaluation_results = json.loads(result.stdout) if result.stdout else None
        if evaluation_results:
            baseline_score = evaluation_results.get("baseline_score", 0)
            custom_prompt_score = evaluation_results.get("custom_prompt_score", 0)
            
            # Visualize results
            st.write("### Evaluation Results")
            st.write("Baseline Score:", baseline_score)
            st.write("Custom Prompt Score:", custom_prompt_score)
            
            st.bar_chart({
                "Scores": [baseline_score, custom_prompt_score]
            }, width=400, height=300)
        else:
            st.warning("No results available from the evaluation.")
    else:
        st.error("There was an error running the evaluation.")
        st.write(result.stderr)
