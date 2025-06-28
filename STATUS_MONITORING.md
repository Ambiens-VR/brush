# Status Monitoring Feature

This document describes the new status monitoring feature that allows external processes (like Python scripts) to monitor Brush training progress in real-time.

## Overview

The status monitoring feature saves training progress information to a JSON file that can be read by external processes. This solves the problem of communicating with the Brush training process from other applications, particularly Python scripts.

## Usage

### Enabling Status Monitoring

To enable status monitoring, use the `--save-status` flag when running Brush:

```bash
# Basic usage with default status file name
cargo run --release -- /path/to/dataset --save-status

# Custom status file name
cargo run --release -- /path/to/dataset --save-status --status-filename my_training_status.json

# Custom export path (status file will be saved there too)
cargo run --release -- /path/to/dataset --save-status --export-path ./output
```

### Command Line Options

- `--save-status`: Enable status file generation (default: false)
- `--status-filename`: Name of the status JSON file (default: "training_status.json")
- `--export-path`: Directory where status file and exports are saved (default: ".")

### Status File Format

The status file is a JSON file with the following structure:

```json
{
  "current_iteration": 1500,
  "total_iterations": 10000,
  "progress_percentage": 15.0,
  "elapsed_time_seconds": 120.5,
  "estimated_remaining_seconds": 685.5,
  "current_splat_count": 50000,
  "last_eval_psnr": 28.5,
  "last_eval_ssim": 0.85,
  "export_path": "./output",
  "current_export_file": "export_01500.ply",
  "status": "training",
  "last_updated": "2025-06-28T09:34:56Z"
}
```

### Status Values

The `status` field can have the following values:

- `"starting"`: Training is initializing
- `"training"`: Normal training in progress
- `"evaluating"`: Running evaluation on test set
- `"exporting"`: Saving PLY file
- `"completed"`: Training finished successfully
- `"error"`: Training failed (not currently implemented)

## Python Integration

### Basic Example

```python
import json
import time
from pathlib import Path

def monitor_training(status_file_path):
    status_file = Path(status_file_path)

    while True:
        if status_file.exists():
            with open(status_file, 'r') as f:
                status = json.load(f)

            print(f"Progress: {status['progress_percentage']:.1f}% "
                  f"({status['current_iteration']}/{status['total_iterations']})")

            if status['status'] == 'completed':
                print(f"Training completed! Output: {status['current_export_file']}")
                break

        time.sleep(1)

# Usage
monitor_training('./training_status.json')
```

### Advanced Example

See `examples/status_monitoring.py` for a complete monitoring script with:

- Real-time progress updates
- Formatted time estimates
- Evaluation metrics display
- Export file tracking
- Error handling

## Use Cases

### 1. Python Training Orchestration

```python
import subprocess
import json
from pathlib import Path

def run_brush_training(dataset_path, output_dir):
    # Start Brush training
    process = subprocess.Popen([
        'cargo', 'run', '--release', '--',
        dataset_path,
        '--save-status',
        '--export-path', output_dir,
        '--status-filename', 'status.json'
    ])

    # Monitor progress
    status_file = Path(output_dir) / 'status.json'
    while process.poll() is None:  # Process still running
        if status_file.exists():
            with open(status_file, 'r') as f:
                status = json.load(f)

            # Your custom logic here
            yield status

        time.sleep(1)

    return process.returncode
```

### 2. Web Dashboard

```python
from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route('/api/training-status')
def get_training_status():
    try:
        with open('training_status.json', 'r') as f:
            status = json.load(f)
        return jsonify(status)
    except FileNotFoundError:
        return jsonify({'error': 'Training not started'}), 404

if __name__ == '__main__':
    app.run(debug=True)
```

### 3. Jupyter Notebook Integration

```python
import json
import time
from IPython.display import display, clear_output
import matplotlib.pyplot as plt

def plot_training_progress(status_file_path):
    iterations = []
    psnr_values = []

    while True:
        try:
            with open(status_file_path, 'r') as f:
                status = json.load(f)

            if status.get('last_eval_psnr'):
                iterations.append(status['current_iteration'])
                psnr_values.append(status['last_eval_psnr'])

                clear_output(wait=True)
                plt.figure(figsize=(10, 6))
                plt.plot(iterations, psnr_values, 'b-o')
                plt.xlabel('Iteration')
                plt.ylabel('PSNR')
                plt.title('Training Progress')
                plt.grid(True)
                plt.show()

            if status['status'] == 'completed':
                break

        except (FileNotFoundError, json.JSONDecodeError):
            pass

        time.sleep(5)
```

## Implementation Details

### File Update Frequency

The status file is updated at the following points:

1. **Training start**: Initial status with "starting"
2. **Every 5 training steps**: Progress update with "training"
3. **During evaluation**: Status changes to "evaluating"
4. **During export**: Status changes to "exporting" with export filename
5. **Training completion**: Final status with "completed"

### Performance Impact

The status file writing has minimal performance impact:

- Only writes when `--save-status` is enabled
- Uses async file I/O
- Small JSON files (< 1KB)
- Errors in status writing don't affect training

### Thread Safety

The status file is written atomically to prevent corruption when read by external processes.

## Troubleshooting

### Status File Not Created

- Ensure `--save-status` flag is used
- Check that the export directory is writable
- Verify the process has started training (not just viewing)

### Corrupted JSON

- The monitoring script should handle `json.JSONDecodeError`
- Status file is written atomically, corruption is rare
- If persistent, check disk space and permissions

### Missing Fields

- Some fields (like `last_eval_psnr`) are only available after evaluation
- Use `.get()` method in Python to handle optional fields safely

## Future Enhancements

Potential improvements for future versions:

- Error status reporting
- More detailed memory usage information
- Training loss history
- Checkpoint information
- Real-time image previews
