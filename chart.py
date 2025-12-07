import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image


# Set global seaborn style for a professional look
sns.set_style("whitegrid")
sns.set_context("talk")  # larger fonts, good for presentations

def generate_data(n_per_channel=250, random_state=42):
    rng = np.random.default_rng(random_state)

    channels = ["Email", "Chat", "Phone", "Social Media"]
    data = []

    for ch in channels:
        if ch == "Email":
            # Email usually slower, wider spread
            response = rng.normal(loc=45, scale=15, size=n_per_channel)
        elif ch == "Chat":
            # Chat generally fastest
            response = rng.normal(loc=10, scale=5, size=n_per_channel)
        elif ch == "Phone":
            # Phone moderate
            response = rng.normal(loc=25, scale=8, size=n_per_channel)
        else:  # Social Media
            response = rng.normal(loc=35, scale=10, size=n_per_channel)

        # No negative times
        response = np.clip(response, 1, None)

        for r in response:
            data.append({"channel": ch, "response_time_minutes": r})

    return pd.DataFrame(data)

def main():
    df = generate_data()

    # Create 512x512 px figure: 8 in * 64 dpi = 512 px
    plt.figure(figsize=(8, 8))

    palette = sns.color_palette("viridis", n_colors=df["channel"].nunique())

    sns.violinplot(
        data=df,
        x="channel",
        y="response_time_minutes",
        hue="channel",
        palette=palette,
        inner="quartile",
        cut=0,
        legend=False,
    )

    plt.title("Customer Support Response Time Distribution by Channel")
    plt.xlabel("Support Channel")
    plt.ylabel("Response Time (minutes)")

    # Optional: you can skip tight_layout to avoid further shrinking
    # plt.tight_layout()

    # Force figure size
    fig = plt.gcf()
    fig.set_size_inches(8, 8)

    # Save to temp, then resize exactly to 512x512
    temp_name = "chart_temp.png"
    plt.savefig(temp_name, dpi=64)
    plt.close()

    from PIL import Image
    img = Image.open(temp_name)
    img = img.resize((512, 512), Image.LANCZOS)
    img.save("chart.png")


if __name__ == "__main__":
    main()
