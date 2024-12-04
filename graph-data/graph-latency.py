import csv
import sys
import matplotlib.pyplot as plt


color_map = {
    "Read": "BLUE",
    "Write": "RED",
    "Compute": "PURPLE",
    "Quick": "PINK"
}

def read_csv(file_path):
    data = []
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return data

def avg_latency_bar_graph(data, output_file):
    labels = [dict["Label"] for dict in data]
    values = [int(dict["Average"]) for dict in data]

    # Define color mapping for specific labels
    color_map = {
        'Write': 'red',
        'Read': 'blue',
        'Compute': 'green',
        'Quick': 'orange'
    }

    # Assign colors to bars based on the labels
    bar_colors = [color_map.get(category.split()[0], 'gray') for category in labels]

    # Creating the bar graph
    plt.bar(labels, values, color=bar_colors)

    # Adding labels and title
    plt.xlabel('Endpoint and Concurrency level')
    plt.ylabel('Time (ms)')
    plt.title('Benchmark Average Latency')

    # Set y-axis limits
    plt.ylim(0, max(values))
    plt.xticks(rotation=90)

    # Add legend (key) for the colors
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in color_map.values()]
    labels = list(color_map.keys())
    plt.legend(handles, labels, title="Categories", loc='upper left', bbox_to_anchor=(1, 1))

    # Save graph
    plt.savefig(f'{output_file}.png', format='png', dpi=300, bbox_inches='tight')  # Save as a high-resolution PNG

def box_plot():
    data = read_csv("data/all-kubernetes-30sec.csv")
    min_val = int(data[0]["Min"])
    median_val = int(data[0]["Median"])
    max_val = int(data[0]["Max"] ) 
    fig, ax = plt.subplots()
    ax.boxplot([min_val, median_val, max_val],vert=False, patch_artist=True)
    plt.show()

def plot_line(data, line_style):
    apis = list(set([dict["Label"].split()[0] for dict in data]))
    for api in apis:
        x = []
        y = []
        if api != "TOTAL":
            for dict in data:
                if dict["Label"].split()[0] == api:
                    x.append(int(dict["Label"].split()[-1]))
                    y.append(int(dict["Min"]))
            plt.plot(x, y, label=api, linestyle=line_style, color=color_map[api])

def avg_latency_line_graph(data, output_file):

    plot_line(data, '-')

    # Adding labels and title
    plt.xlabel('Number of Concurrent Threads')
    plt.ylabel('Average Time (ms)')
    plt.title('Benchmark Average Latency')
    plt.legend()

    # Save graph
    plt.savefig(f'{output_file}.png', format='png', dpi=300, bbox_inches='tight')  # Save as a high-resolution PNG


def avg_latency_compare(output_file):
    data1 = read_csv("data/all-openfaas-30sec.csv")
    data2 = read_csv("data/all-kubernetes-30sec.csv")

    plot_line(data1, '-.')
    plot_line(data2, '-')
    # Adding labels and title
    plt.xlabel('Number of Concurrent Threads')
    plt.ylabel('Average Time (ms)')
    plt.title('Benchmark Average Latency')
    plt.legend()

    # Save graph
    plt.savefig(f'{output_file}.png', format='png', dpi=300, bbox_inches='tight')  # Save as a high-resolution PNG


if __name__ == "__main__":
    # Check if the file path is provided as an argument
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <path_to_csv_file> <path_to_output_file>")
    else:
        file_path = sys.argv[1]
        output_file_path = sys.argv[2]
        data = read_csv(file_path)
        # avg_latency_bar_graph(data, output_file_path)
        # avg_latency_line_graph(data, output_file_path)
        # avg_latency_compare(output_file_path)
        box_plot()
