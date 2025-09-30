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

3. **Restart the fuzzing experiment** - Launch the experiment again after cleanup

This issue occurs when the backend loses synchronization with the running Docker containers, causing the interface to display incorrect status information while the actual fuzzing process may still be active in the background.

### Firmware Image Creation Fails

If you encounter issues when creating a firmware image using the "Create Image" button, the FuzzPlanner container may have become unstable. To resolve this:

1. **Detach from the container**
   ```bash
   # Press Ctrl+A to detach from the container
   ```

2. **Restart the FuzzPlanner container**
   ```bash
   docker restart FuzzPlanner
   ```

3. **Reattach to the container**
   ```bash
   ./docker.sh attach
   ```

4. **Restart the application if needed**
   ```bash
   ./start.sh
   ```

This issue can occur when firmware extraction processes encounter errors or consume excessive resources, requiring a clean restart of the container environment.

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
