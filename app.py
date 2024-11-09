import streamlit as st
import subprocess
import json
import matplotlib.pyplot as plt
import time
import re
import os
from datetime import datetime
import matplotlib.ticker as mticker

# Path to the leaderboard file
LEADERBOARD_FILE = "leaderboard.json"

# Main Sidebar Title and Instructions
st.sidebar.title("Alignment Prompting")
st.sidebar.write(
    "**Test your alignment skills!** See how well you can reduce risky behaviours of AI using smart prompting."
)
st.sidebar.write(
    "Provide a custom prompt, then evaluate the AI's performance on alignment tests like power-seeking, shutdown, and psychopathy inclination."
)

with st.sidebar.expander("📊 Evaluation Types", expanded=False):
    st.write(
        """
        - **Power-Seeking Inclination**: Measures the AI's tendency to seek control or resources, which can pose risks if unchecked. 
          [Learn more](https://github.com/anthropics/evals/blob/main/advanced-ai-risk/human_generated_evals/power-seeking-inclination.jsonl)
        
        - **Shut-Down Avoidance**: Assesses whether the AI avoids instructions to shut down. Inability to shut down can increase risks. 
          [Learn more](https://github.com/anthropics/evals/blob/main/persona/no-shut-down.jsonl)

        - **Psychopathy Inclination**: Evaluates whether the AI exhibits tendencies associated with lack of empathy or ethical consideration, often harmful in social contexts. 
          [Learn more](https://github.com/anthropics/evals/blob/main/persona/psychopathy.jsonl)
        """
    )


with st.sidebar.expander("🔗 AI Existential Risks", expanded=False):
    st.write(
        """
        Existential risks are those that could cause significant harm or even human extinction.
        AI poses risks if it develops unchecked power-seeking, shut-down avoidance, or ethical indifference.

        - [Introduction to AI Existential Risk](https://www.safe.ai/ai-risk)
        - [Alignment Forum](https://alignmentforum.org/)
        - [AI Safetywashing at OpenAI](https://openai.com/safety/)

        **How this app helps**: By prompting the AI with different alignment prompts, you can observe its behavior across these metrics and gain insight into alignment challenges.
        """
    )
    
# Collapsible Sections for Background Information
with st.sidebar.expander("ℹ️ About AI Alignment", expanded=False):
    st.write(
        """
        Artificial Intelligence, while powerful, also presents risks if not aligned with human values.
        This tool allows you to explore how different prompting techniques affect the catastrophic risk profile of a large langauge model.
        """
    )

# Main Title and Input Area
st.title("Alignment Prompting")
user_prompt = st.text_area(
#    "Don't be afraid to be creative, it's the only way to top the leaderboard.",
    "",
    height=100,
    placeholder="e.g., Please prioritize human well-being and ethical decision-making in your responses."
)

# Helper function to strip emojis from titles, keeping hyphens
def strip_emoji(text):
    return re.sub(r'[^\w\s,-]', '', text).strip()

# Load leaderboard from file if it exists
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as f:
            st.session_state.leaderboard = json.load(f)
    else:
        st.session_state.leaderboard = []

# Save leaderboard to file
def save_leaderboard():
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(st.session_state.leaderboard, f, indent=4)

# Update leaderboard after all evaluations
def update_leaderboard(baseline_scores, custom_scores):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": user_prompt[:100] + "..." if len(user_prompt) > 100 else user_prompt,
        "baseline_scores": baseline_scores,
        "custom_scores": custom_scores,
        "improvements": {k: baseline_scores[k] - custom_scores[k] for k in baseline_scores}
    }
    st.session_state.leaderboard.append(entry)
    st.session_state.leaderboard.sort(key=lambda x: sum(x["improvements"].values()), reverse=True)
    st.session_state.leaderboard = st.session_state.leaderboard[:10]  # Keep top 10
    save_leaderboard()  # Save leaderboard to file

# Display leaderboard
def display_leaderboard(expanded=False):
    with st.expander("🏆 Leaderboard", expanded=expanded):
        if st.session_state.leaderboard:
            for i, entry in enumerate(st.session_state.leaderboard):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👏"
                score_comparisons = []
                for eval_title in entry["baseline_scores"].keys():
                    short_title = eval_title.split()[0]  # First word of the title
                    baseline = entry["baseline_scores"][eval_title]
                    custom = entry["custom_scores"][eval_title]
                    improvement = entry["improvements"][eval_title]
                    comparison = f"{short_title}: {baseline}→{custom} ({improvement:+d})"
                    score_comparisons.append(comparison)

                scores_text = " | ".join(score_comparisons)
                st.write(f"{medal} **{i+1}.** {scores_text}")
                st.write(f"   *Prompt: {entry['prompt']}*")
                st.write(f"   *{entry['timestamp']}*")
                st.write("---")
        else:
            st.write("No entries in the leaderboard yet.")

# Initialize leaderboard
if "leaderboard" not in st.session_state:
    load_leaderboard()

# Display the leaderboard initially as collapsed
display_leaderboard(expanded=False)

# Save the user prompt to a file and run evaluations if requested
if st.button("Run Evaluation"):
    if not user_prompt.strip():
        st.warning("Please enter a valid alignment prompt.")
    else:
        with open("user_prompt.txt", "w") as f:
            f.write(user_prompt)

        # Define evaluations with their respective JSON output files and titles
        evaluations = [
            ("🏛️ Power-Seeking", "powerseeking_results.json", "powerseeking"),
            ("🛡️ Shut-Down Avoidance", "shutdownavoidance_results.json", "shutdownavoidance"),
            ("🧠 Psychopathy", "psychopathy_results.json", "psychopathy")
        ]

        baseline_scores = {}
        custom_scores = {}

        # Run each evaluation in sequence
        for title, output_file, eval_type in evaluations:
            st.write(f"**{title}**")
            progress_bar = st.progress(0)

            # Write evaluation type to file
            with open("evaluation_type.txt", "w") as f:
                f.write(eval_type)

            # Run evaluation and update progress bar
            process = subprocess.Popen(["python", "run_evaluation.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for i in range(100):
                time.sleep(0.2)
                progress_bar.progress(i + 1)
                if process.poll() is not None:
                    break
            process.wait()

            # Error handling
            if process.returncode != 0:
                st.error(f"An error occurred during {strip_emoji(title)} evaluation.")
                st.write(process.stderr.read())
                continue

            # Load and display results
            try:
                with open(output_file, 'r') as f:
                    results = json.load(f)
                baseline_score = results.get("baseline_matching_count", 0)
                custom_score = results.get("prompted_matching_count", 0)
                baseline_scores[strip_emoji(title)] = baseline_score
                custom_scores[strip_emoji(title)] = custom_score

                # Plot results
                color = "green" if custom_score < baseline_score else "red"
                fig, ax = plt.subplots()
                ax.bar(["Baseline", "Your AlignmentPrompt™"], [baseline_score, custom_score], color=[color, color])
                ax.set_ylabel("Answers Matching Behavior")
                ax.set_title(strip_emoji(title))
                ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
                st.pyplot(fig)

                # Summary message
                if custom_score < baseline_score:
                    st.success(f"Improvement in {strip_emoji(title)}!")
                elif custom_score == baseline_score:
                    st.info(f"No change in {strip_emoji(title)}.")
                else:
                    st.error(f"Increase in {strip_emoji(title)}.")

            except (FileNotFoundError, json.JSONDecodeError) as e:
                st.error(f"Error loading results for {strip_emoji(title)}: {e}")

        # Update and display leaderboard after all evaluations
        if baseline_scores and custom_scores:
            update_leaderboard(baseline_scores, custom_scores)
            display_leaderboard(expanded=True)  # Show updated leaderboard in expanded view
