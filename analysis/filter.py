import json

# Read JSON data from "a.json"
with open("results/DAP-2330_1.01/dynamic_analysis/run_1/data/interactions.json", "r") as a_json_file:
    a_json_data = json.load(a_json_file)

# Read JSON data from "b.json"
with open("results/DAP-2330_1.01/dynamic_analysis/run_1/data/processes.json", "r") as b_json_file:
    b_json_data = json.load(b_json_file)

# Find elements with channel containing ":80" in a.json
matching_elements = [element for element in a_json_data if ":80" in element.get("channel", "")]

# Ensure we found at least one matching element
if matching_elements:
    # Extract the "time" values for the first and second "sinks" elements
    element = matching_elements[0]  # Assuming we are interested in the first matching element
    sinks = element.get("sinks", [])
    if len(sinks) >= 2:
        time_a = sinks[0]["time"]
        print(time_a)
        time_b = sinks[1]["time"]
        print(time_b)

        # Filter b.json data based on "id" and create a mapping from "id" to "executable"
        id_to_executable_mapping = {item["id"]: item["executable"] for item in b_json_data}

        # Function to replace "pid" with "executable" if there's a match
        def replace_pid_with_executable(element):
            if "sources" in element:
                for source in element["sources"]:
                    source_pid = source.get("pid", "")
                    if source_pid in id_to_executable_mapping:
                        source["pid"] += "(" + id_to_executable_mapping[source_pid] + ")"
            if "sinks" in element:
                for sink in element["sinks"]:
                    sink_pid = sink.get("pid", "")
                    if sink_pid in id_to_executable_mapping:
                        sink["pid"] += "(" + id_to_executable_mapping[sink_pid] + ")"

        # Iterate through elements in a.json and replace "pid" with "executable" if applicable
        for element in a_json_data:
            replace_pid_with_executable(element)

        # Filter a.json data based on the time range between A and B
        filtered_data = [element for element in a_json_data if "sources" in element and "sinks" in element]
        filtered_data = [
            element
            for element in filtered_data
            if any(time_a <= source["time"] < time_b for source in element["sources"])
            or any(time_a <= sink["time"] < time_b for sink in element["sinks"])
        ]

        # Print the updated JSON data
        c_json_data = json.dumps(filtered_data, indent=2)
    else:
        print("Matching element does not have at least two sinks.")
else:
    print("No matching elements found with channel containing ':80'.")

data = filtered_data

# Define a function to write an operation to the log file
def write_operation(log_file, source_pid, channel, sink_pid, source_time, sink_time):
    if channel != "NULL":
        if source_pid:
            log_file.write(f"({source_time}) ({source_pid}) ----->  ({channel}) -------> ({sink_time}) ({sink_pid})\n")
        else:
            log_file.write(f"({channel}) -------> ({sink_time}) ({sink_pid})\n")
    else:
        log_file.write(f"STARTED ({source_time}) ({source_pid})\n")

# Create a list to store the operations
operations = []

for entry in data:
    sources = entry["sources"]
    sinks = entry["sinks"]
    channel = entry["channel"]

    if sources:
        for source, sink in zip(sources, sinks):
            source_pid = source["pid"]
            source_time = source["time"]
            sink_pid = sink["pid"]
            sink_time = sink["time"]
            operations.append((source_time, source_pid, channel, sink_time, sink_pid))
    else:
        for sink in sinks:
            source_pid = ""
            source_time = sink["time"]
            sink_pid = sink["pid"]
            sink_time = sink["time"]
            operations.append((source_time, source_pid, channel, sink_time, sink_pid))

# Extract and sort lines from "b.json"
b_json_lines = []

for entry in b_json_data:
    start_time = entry["start_time"]
    pid = entry["id"]+"("+entry["executable"]+")"
    if time_a <= int(start_time) <= time_b:
        operations.append((start_time, pid, "NULL", 0, ""))

# Sort the operations based on timestamps, treating empty timestamps as infinity
operations.sort(key=lambda x: (x[0] or float("inf"), x[3]))

# Open a log file for writing
with open("log.txt", "w") as log_file:
    # Sort the operations into two lists: one for lines without sources and one for lines with sources
    operations_without_sources = []
    operations_with_sources = []

    for operation in operations:
        source_time, source_pid, channel, sink_time, sink_pid = operation
        # Check if the operation meets the criteria for lines without sources
        if (not source_time or (source_time == 0)) and (time_a <= sink_time <= time_b):
            operations_without_sources.append(operation)
        # Check if the operation meets the criteria for lines with sources
        elif source_time and time_a <= source_time <= time_b:
            operations_with_sources.append(operation)

    # Write lines without sources first
    for operation in operations_without_sources:
        source_time, source_pid, channel, sink_time, sink_pid = operation
        write_operation(log_file, source_pid, channel, sink_pid, source_time, sink_time)

    # Then write lines with sources
    for operation in operations_with_sources:
        source_time, source_pid, channel, sink_time, sink_pid = operation
        write_operation(log_file, source_pid, channel, sink_pid, source_time, sink_time)

print("Log file 'log.txt' has been created and sorted by timestamps.")

