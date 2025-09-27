# FuzzPlanner

A visual analytics tool for designing fuzzing campaigns on firmware. FuzzPlanner helps security researchers analyze firmware behavior, identify attack surfaces, and plan effective fuzzing strategies through an intuitive web interface.


## Features

- **🔍 Firmware Analysis**: Analyze binary execution patterns and interactions during firmware emulation
- **📊 Visual Analytics**: Interactive timeline, binary tables, and network graphs for comprehensive analysis
- **🎯 Target Selection**: Identify optimal fuzzing targets based on data flows and vulnerabilities
- **⚡ Campaign Management**: Plan, execute, and monitor fuzzing experiments through a unified interface
- **📈 Progress Tracking**: Real-time monitoring of fuzzing progress with detailed statistics

## Quick Start

### Prerequisites

- **Docker** (required for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FuzzPlanner
   ```

2. **Build and setup the Docker environment**
   ```bash
   ./setup.sh
   ```

3. **Run the application**
   ```bash
   # Start the container
   ./docker.sh run

   # Attach to the container
   ./docker.sh attach

   # Inside the container, start the application
   ./start.sh
   ```

4. **Access the interface**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:4000

5. **Shutdown the application**
   - Press `Ctrl+C` to stop the application
   - Press `Ctrl+A` to detach from the container

The setup script will automatically:
- Build the Docker image using docker.sh
- Install all dependencies inside the container
- Configure the environment for FuzzPlanner
- Commit the configured image for future use

## Usage

### 1. Upload Firmware
- Upload firmware images (supports various formats)
- Configure emulation parameters
- Start firmware emulation in QEMU

### 2. Analyze Execution
- **Timeline View**: Explore temporal behavior of binary execution
- **Binary Table**: Examine all executed binaries with interaction statistics
- **Binary Graph**: Visualize inter-binary communication and data flows
- **Channel Analysis**: Identify input/output channels and vulnerabilities

### 3. Plan Fuzzing Campaign
- Select promising binary-channel pairs for fuzzing
- Configure fuzzing parameters (dictionaries, engines, etc.)
- Launch experiments with real-time monitoring

### 4. Monitor Results
- Track fuzzing progress with live statistics
- Analyze discovered crashes and hangs
- Export results for further investigation

## Troubleshooting

### Fuzzing Experiments Stuck in "REPLAYING" Phase

If your fuzzing experiments get stuck in the "REPLAYING" phase and don't progress, this typically indicates a mismatch between the target PC address identified during data-channel analysis and the actual PC address during fuzzing emulation. To resolve this:

1. **Cancel the stuck experiment** - Stop the current fuzzing experiment
2. **Restart the experiment** - Try launching the fuzzing experiment again, or
3. **Re-analyze the data channel** - In the Run Manager, perform a new data-channel analysis on the target data channel you intend to fuzz

This issue occurs because the "target pc" to hook (output from the data-channel analysis) sometimes doesn't match the actual program counter during the fuzzing experiment emulation, causing the fuzzer to wait indefinitely for the expected execution point.

### Fuzzing Experiments Skip Phases and Go Directly to "COMPLETED"

If your fuzzing experiments skip the "BOOTING" and "REPLAYING" phases and go directly to "COMPLETED" status, this indicates a backend desynchronization issue. The fuzzing Docker container is likely still running even though the interface shows it as completed. To resolve this:

1. **Force remove the Docker container**
   ```bash
   docker rm -f <fuzz_container_name>
   ```

2. **Clean up related temporary data**
   ```bash
   # Remove fuzzing statistics
   rm -rf tmp/fuzz_stat/<experiment_id>

   # Remove fuzzing experiment data
   rm -rf tmp/fuzz_experiments/<experiment_id>
   ```

3. **Restart the fuzzing experiment** - Launch the experiment again after cleanup

This issue occurs when the backend loses synchronization with the running Docker containers, causing the interface to display incorrect status information while the actual fuzzing process may still be active in the background.

## Architecture

```
FuzzPlanner/
├── server_app.py           # Flask backend server
├── engine.py               # Execution engine
├── scheduler.py           # Container orchestration
├── webapp/                # React frontend
│   ├── src/components/    # UI components
│   ├── src/modules/       # Main application modules
│   └── src/hooks/         # Custom React hooks
├── FirmAFL/              # Modified AFL for firmware
├── scripts/              # Analysis and utility scripts
└── config/               # Configuration files
```

## Key Components

- **Timeline**: Temporal analysis of firmware execution
- **Binary Table**: Statistical overview of executed binaries
- **Binary Graph**: Network visualization of binary interactions
- **Target Picker**: Binary and data channel selection interface
- **Experiment Launcher**: Fuzzing campaign configuration
- **Progress Monitor**: Real-time fuzzing statistics and results

## Publication

This tool is based on research presented at VizSec 2023:

> Coppa, Emilio, Alessio Izzillo, Riccardo Lazzeretti e Simone Lenti. **"FuzzPlanner: Visually Assisting the Design of Firmware Fuzzing Campaigns."** *2023 IEEE Symposium on Visualization for Cyber Security (VizSec).* IEEE, 2023.
