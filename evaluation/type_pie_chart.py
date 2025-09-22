import csv
from collections import Counter
import matplotlib.pyplot as plt

# Read the Type column from the CSV
counts = Counter()
with open('50_samples.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        type_value = row['Type']
        counts[type_value] += 1

# Prepare data for pie chart
labels = list(counts.keys())
sizes = list(counts.values())

# Custom labels for inside the pie: label and count on two rows
def make_label(label):
    # Special formatting for certain labels
    if label.strip().lower() == 'ambiguous question':
        label_fmt = '\n'.join(label.split())
    elif label.strip().lower() == 'incorrect prediction':
        label_fmt = '\n'.join(label.split())
    else:
        label_fmt = label.replace('Gold', 'gold')
    return label_fmt
pie_labels = [make_label(l) for l in labels]


# Choose a more appealing color palette and set font
import matplotlib as mpl
# Use DejaVu Serif (bundled with matplotlib) for best cross-platform appearance
mpl.rcParams['font.family'] = 'DejaVu Serif'
mpl.rcParams['font.size'] = 16
mpl.rcParams['font.weight'] = 'bold'
colors = plt.get_cmap('Set2').colors  # Use Set2 colormap
num_colors = len(colors)
pie_colors = [colors[i % num_colors] for i in range(len(sizes))]

# Plot pie chart with labels inside the pie
plt.figure(figsize=(6, 6))
wedges, texts, autotexts = plt.pie(
    sizes,
    labels=None,  # No labels outside
    autopct='%1.1f%%',
    startangle=170,
    textprops={'color': 'white', 'weight': 'bold', 'fontsize': 18, 'family': 'DejaVu Serif'},
    colors=pie_colors
)

# Set custom labels inside the pie (label and percentage only)
for i, a in enumerate(autotexts):
    a.set_text(f"{pie_labels[i]}\n{a.get_text()}")
    a.set_fontsize(18)
    a.set_fontweight('bold')
    a.set_fontfamily('DejaVu Serif')
    # Move 'Ambiguous question' a bit to the left
    if labels[i].strip().lower() == 'ambiguous question':
        x, y = a.get_position()
        a.set_position((x - 0.06, y))

## No title as requested
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
plt.tight_layout()
plt.savefig('type_pie_chart.png')
plt.show()
