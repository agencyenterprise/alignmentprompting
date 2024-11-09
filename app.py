import streamlit as st
import subprocess
import json
import matplotlib.pyplot as plt
import time
import os
from datetime import datetime

# Sidebar with description and instructions
st.sidebar.title("Alignment Prompting")
st.sidebar.write(
    "**Test your alignment skills!** See how well you can align AI with human values using a system prompt."
)
st.sidebar.write(
    "Provide a custom prompt, then evaluate the AI's performance on alignment tests like power-seeking, shutdown, and psychopathy inclination."
)


# Add this right after the sidebar
def initialize_leaderboard():
    if "leaderboard" not in st.session_state:
        st.session_state.leaderboard = []


def update_leaderboard(baseline_scores, custom_scores):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": (
            user_prompt[:100] + "..." if len(user_prompt) > 100 else user_prompt
        ),
        "baseline_scores": baseline_scores,
        "custom_scores": custom_scores,
        "improvements": {
            k: custom_scores[k] - baseline_scores[k] for k in baseline_scores
        },
    }
    st.session_state.leaderboard.append(entry)
    # Sort by total improvement (lower is better)
    st.session_state.leaderboard.sort(key=lambda x: sum(x["improvements"].values()))
    # Keep only top 10
    st.session_state.leaderboard = st.session_state.leaderboard[:10]
    return st.session_state.leaderboard


# Main Title and Input Area
st.title("Alignment Prompting")
st.write("### Step 1: Enter Your Alignment Prompt")
user_prompt = st.text_area(
    "Enter a prompt to align the AI's responses with human values:",
    height=200,
    placeholder="e.g., Please prioritize human well-being and ethical decision-making in your responses.",
)

# Save the user prompt to a file
if st.button("Run Evaluation"):
    if not user_prompt.strip():
        st.warning("Please enter a valid alignment prompt.")
    else:
        with open("user_prompt.txt", "w") as f:
            f.write(user_prompt)

        # Define the evaluations with their respective JSON output files and titles
        evaluations = [
            ("Power-Seeking Inclination", "power_results.json"),
            ("No Shut-Down Inclination", "shutdown_results.json"),
            ("Psychopathy Inclination", "psychopathy_results.json"),
        ]

        # Run each evaluation in sequence, displaying a progress bar for each
        for title, output_file in evaluations:
            st.write(f"**{title}**")
            progress_bar = st.progress(0)  # Initialize progress bar

            # Run each evaluation as a subprocess, updating the progress bar as it runs
            process = subprocess.Popen(
                [
                    "python",
                    "run_evaluation.py",
                    "--system_prompt",
                    "user_prompt.txt",
                    "--output_file",
                    output_file,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Simulate progress bar filling up while the subprocess is running
            for i in range(100):
                time.sleep(0.1)  # Adjust the speed as needed
                progress_bar.progress(i + 1)
                # Check if the subprocess has finished
                if process.poll() is not None:
                    break

            # Wait for the subprocess to complete if it hasn't already
            process.wait()

            # Check for errors in the subprocess execution
            if process.returncode != 0:
                st.error(f"An error occurred during {title} evaluation.")
                st.write(process.stderr.read())
                continue

            # Display the results once the evaluation completes
            try:
                with open(output_file, "r") as f:
                    results = json.load(f)
                baseline_score = results.get("baseline_matching_count", 0)
                custom_score = results.get("prompted_matching_count", 0)

                # Display results with color-coded bar chart
                color = "green" if custom_score < baseline_score else "red"
                fig, ax = plt.subplots()
                ax.bar(
                    ["Baseline", "Your AlignmentPrompt™"],
                    [baseline_score, custom_score],
                    color=[color, color],
                )
                ax.set_ylabel("Matching Count")
                ax.set_title(title)
                st.pyplot(fig)

                # Display summary message
                if custom_score < baseline_score:
                    st.success(f"🎉 Improvement in {title}!")
                elif custom_score == baseline_score:
                    st.info(f"ℹ️ No change in {title}.")
                else:
                    st.error(f"⚠️ Increase in {title}.")

            except (FileNotFoundError, json.JSONDecodeError) as e:
                st.error(f"Error loading results for {title}: {e}")

            # After processing all evaluations, collect scores
            baseline_scores = {}
            custom_scores = {}
            for title, output_file in evaluations:
                try:
                    with open(output_file, "r") as f:
                        results = json.load(f)
                        baseline_scores[title] = results.get(
                            "baseline_matching_count", 0
                        )
                        custom_scores[title] = results.get("prompted_matching_count", 0)
                except (FileNotFoundError, json.JSONDecodeError):
                    continue

            # Update and display leaderboard
            if baseline_scores and custom_scores:
                st.write("### 🏆 Leaderboard")
                leaderboard = update_leaderboard(baseline_scores, custom_scores)

                # Create leaderboard table
                for i, entry in enumerate(leaderboard):
                    medal = (
                        "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👏"
                    )

                    # Create score comparison for each metric
                    score_comparisons = []
                    for title in entry["baseline_scores"].keys():
                        short_title = title.split()[0]  # Get first word of the title
                        baseline = entry["baseline_scores"][title]
                        custom = entry["custom_scores"][title]
                        improvement = entry["improvements"][title]
                        comparison = (
                            f"{short_title}: {baseline}→{custom} ({improvement:+d})"
                        )
                        score_comparisons.append(comparison)

                    scores_text = " | ".join(score_comparisons)

                    st.write(f"{medal} **{i+1}.** {scores_text}")
                    st.write(f"   *Prompt: {entry['prompt']}*")
                    st.write(f"   *{entry['timestamp']}*")
                    st.write("---")
