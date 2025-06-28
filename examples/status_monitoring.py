#!/usr/bin/env python3
"""
Example script showing how to monitor Brush training progress from Python.

This script demonstrates how to use the new --save-status feature to monitor
training progress by reading the JSON status file that Brush creates during training.

Usage:
    # Start training with status monitoring enabled
    cargo run --release -- /path/to/dataset --save-status --status-filename training_status.json

    # In another terminal, run this monitoring script
    python examples/status_monitoring.py ./training_status.json
"""

import json
import time
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone


def format_duration(seconds):
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def monitor_training_progress(status_file_path, update_interval=1.0):
    """
    Monitor training progress by reading the status file.
    
    Args:
        status_file_path: Path to the training status JSON file
        update_interval: How often to check for updates (seconds)
    """
    status_file = Path(status_file_path)
    last_iteration = -1
    
    print(f"Monitoring training progress from: {status_file}")
    print("Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            try:
                if not status_file.exists():
                    print("Status file not found, waiting for training to start...")
                    time.sleep(update_interval)
                    continue
                
                with open(status_file, 'r') as f:
                    status = json.load(f)
                
                # Only print update if iteration changed
                current_iter = status['current_iteration']
                if current_iter != last_iteration:
                    last_iteration = current_iter
                    
                    # Format the status update
                    progress = status['progress_percentage']
                    elapsed = format_duration(status['elapsed_time_seconds'])
                    remaining = format_duration(status['estimated_remaining_seconds'])
                    splat_count = status['current_splat_count']
                    train_status = status['status']
                    
                    # Build status line
                    status_line = (
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"Iter {current_iter}/{status['total_iterations']} "
                        f"({progress:.1f}%) | "
                        f"Elapsed: {elapsed} | "
                        f"Remaining: {remaining} | "
                        f"Splats: {splat_count:,} | "
                        f"Status: {train_status}"
                    )
                    
                    # Add evaluation metrics if available
                    if status.get('last_eval_psnr') is not None:
                        psnr = status['last_eval_psnr']
                        ssim = status['last_eval_ssim']
                        status_line += f" | PSNR: {psnr:.2f} | SSIM: {ssim:.3f}"
                    
                    # Add export info if available
                    if status.get('current_export_file'):
                        export_file = status['current_export_file']
                        status_line += f" | Last export: {export_file}"
                    
                    print(status_line)
                    
                    # Check if training is completed
                    if train_status == 'completed':
                        print(f"\n✅ Training completed!")
                        if status.get('current_export_file'):
                            print(f"Final output: {status['export_path']}/{status['current_export_file']}")
                        break
                    elif train_status == 'error':
                        print(f"\n❌ Training failed!")
                        break
                        
            except json.JSONDecodeError:
                print("Status file corrupted, retrying...")
            except FileNotFoundError:
                print("Status file disappeared, waiting...")
            except KeyError as e:
                print(f"Missing key in status file: {e}")
            
            time.sleep(update_interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor Brush training progress",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'status_file',
        help='Path to the training status JSON file'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Update interval in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    monitor_training_progress(args.status_file, args.interval)


if __name__ == '__main__':
    main()
