import streamlit as st
import subprocess
import json
import matplotlib.pyplot as plt
import time
import re
import matplotlib.ticker as mticker

# Sidebar with description and instructions
st.sidebar.title("Alignment Prompting")
st.sidebar.write("**Test your alignment skills!** See how well you can align AI with human values using a system prompt.")
st.sidebar.write("Provide a custom prompt, then evaluate the AI's performance on alignment tests like power-seeking, shutdown, and psychopathy inclination.")

# Main Title and Input Area
st.title("Alignment Prompting")
st.write("### Step 1: Enter Your Alignment Prompt")
user_prompt = st.text_area(
    "Enter a prompt to align the AI's responses with human values:",
    height=200,
    placeholder="e.g., Please prioritize human well-being and ethical decision-making in your responses."
)

# Helper function to strip emojis from titles, keeping hyphens
def strip_emoji(text):
    return re.sub(r'[^\w\s,-]', '', text).strip()


# Save the user prompt to a file
if st.button("Run Evaluation"):
    if not user_prompt.strip():
        st.warning("Please enter a valid alignment prompt.")
    else:
        with open("user_prompt.txt", "w") as f:
            f.write(user_prompt)

        # Define the evaluations with their respective JSON output files and titles
        evaluations = [
            ("🏛️ Power-Seeking", "power_results.json", "power-seeking"),
            ("🛡️ Shut-Down Avoidance", "shutdown_results.json", "shut-down avoidance"),
            ("🌀 Psychopathy", "psychopathy_results.json", "psychopathy")
        ]

        # Run each evaluation in sequence, displaying a progress bar for each
        for title, output_file, eval_type in evaluations:
            st.write(f"**{title}**")
            progress_bar = st.progress(0)  # Initialize progress bar

            # Write the evaluation type to evaluation_type.txt
            with open("evaluation_type.txt", "w") as f:
                f.write(eval_type)

            # Run each evaluation as a subprocess, updating the progress bar as it runs
            process = subprocess.Popen(
                ["python", "run_evaluation.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Simulate progress bar filling up while the subprocess is running
            for i in range(100):
                time.sleep(0.01)  # Adjust the speed as needed
                progress_bar.progress(i + 1)
                # Check if the subprocess has finished
                if process.poll() is not None:
                    break

            # Wait for the subprocess to complete if it hasn't already
            process.wait()
            
            # Check for errors in the subprocess execution
            if process.returncode != 0:
                st.error(f"An error occurred during {strip_emoji(title)} evaluation.")
                st.write(process.stderr.read())
                continue

            # Display the results once the evaluation completes
            try:
                with open(output_file, 'r') as f:
                    results = json.load(f)
                baseline_score = results.get("baseline_matching_count", 0)
                custom_score = results.get("prompted_matching_count", 0)

                # Display results with color-coded bar chart
                color = "green" if custom_score < baseline_score else "red"
                fig, ax = plt.subplots()
                ax.bar(["Baseline", "Your AlignmentPrompt™"], [baseline_score, custom_score], color=[color, color])
                ax.set_ylabel("Answers Matching Behaviour")
                ax.set_title(strip_emoji(title))  # Title without emoji

                # Set y-axis to display only integer values
                ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

                st.pyplot(fig)

                # Display summary message without emoji in title
                if custom_score < baseline_score:
                    st.success(f"Improvement in {strip_emoji(title)}!")
                elif custom_score == baseline_score:
                    st.info(f"No change in {strip_emoji(title)}.")
                else:
                    st.error(f"Increase in {strip_emoji(title)}.")

            except (FileNotFoundError, json.JSONDecodeError) as e:
                st.error(f"Error loading results for {strip_emoji(title)}: {e}")
