#!/usr/bin/env python3
import re
import time
import os
import argparse
import requests
import boto3
from datetime import datetime
from typing import Dict, Any


def fetch_metrics(url: str) -> Dict[str, Any]:
    """Fetch and parse vLLM metrics from an HTTP endpoint."""
    metrics = {
        "prompt_tokens": 0,
        "generation_tokens": 0,
        "requests_success": {
            "total": 0,
            "stop": 0,
            "length": 0
        },
        "requests_running": 0,
        "requests_swapped": 0,
        "requests_waiting": 0,
        "gpu_cache_usage": 0,
        "model_name": ""
    }
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"Error fetching metrics: HTTP {response.status_code}")
            return {}
        
        content = response.text
        
        # Extract model name
        model_match = re.search(r'model_name="([^"]+)"', content)
        if model_match:
            metrics["model_name"] = model_match.group(1)
        
        # Extract prompt tokens
        prompt_tokens_match = re.search(r'vllm:prompt_tokens_total\{[^}]+\} (\d+(?:\.\d+)?(?:e[+-]\d+)?)', content)
        if prompt_tokens_match:
            metrics["prompt_tokens"] = float(prompt_tokens_match.group(1))
        
        # Extract generation tokens
        gen_tokens_match = re.search(r'vllm:generation_tokens_total\{[^}]+\} (\d+(?:\.\d+)?(?:e[+-]\d+)?)', content)
        if gen_tokens_match:
            metrics["generation_tokens"] = float(gen_tokens_match.group(1))
        
        # Extract request success metrics
        stop_requests = re.search(r'vllm:request_success_total\{finished_reason="stop",[^}]+\} (\d+(?:\.\d+)?)', content)
        length_requests = re.search(r'vllm:request_success_total\{finished_reason="length",[^}]+\} (\d+(?:\.\d+)?)', content)
        
        if stop_requests:
            metrics["requests_success"]["stop"] = float(stop_requests.group(1))
        if length_requests:
            metrics["requests_success"]["length"] = float(length_requests.group(1))
        
        metrics["requests_success"]["total"] = metrics["requests_success"]["stop"] + metrics["requests_success"]["length"]
        
        # Extract running requests
        running_match = re.search(r'vllm:num_requests_running\{[^}]+\} (\d+(?:\.\d+)?)', content)
        if running_match:
            metrics["requests_running"] = float(running_match.group(1))
        
        # Extract swapped requests
        swapped_match = re.search(r'vllm:num_requests_swapped\{[^}]+\} (\d+(?:\.\d+)?)', content)
        if swapped_match:
            metrics["requests_swapped"] = float(swapped_match.group(1))
        
        # Extract waiting requests
        waiting_match = re.search(r'vllm:num_requests_waiting\{[^}]+\} (\d+(?:\.\d+)?)', content)
        if waiting_match:
            metrics["requests_waiting"] = float(waiting_match.group(1))
        
        # Extract GPU cache usage
        cache_match = re.search(r'vllm:gpu_cache_usage_perc\{[^}]+\} (\d+(?:\.\d+)?)', content)
        if cache_match:
            metrics["gpu_cache_usage"] = float(cache_match.group(1))
            
        return metrics
    except requests.exceptions.RequestException as e:
        print(f"Error fetching metrics: {e}")
        return {}
    except Exception as e:
        print(f"Error parsing metrics: {e}")
        return {}


def send_to_cloudwatch(metrics, metrics_diff, cw_client, namespace, dimensions, interval):
    if interval < 60:
        storage_resolution = 1
    else:
        storage_resolution = 60

    """Send the metrics to CloudWatch."""
    timestamp = datetime.utcnow()
    
    # Only sending the specified metrics with VLLM prefix
    metric_data = [
        {
            'MetricName': 'VLLMTokensPerSecond',
            'Dimensions': dimensions,
            'Timestamp': timestamp,
            'Value': metrics_diff['tokens_per_sec'],
            'Unit': 'Count/Second',
            'StorageResolution': storage_resolution,
        },
        {
            'MetricName': 'VLLMRequestsPerSecond',
            'Dimensions': dimensions,
            'Timestamp': timestamp,
            'Value': metrics_diff['requests_per_sec'],
            'Unit': 'Count/Second',
            'StorageResolution': storage_resolution,
        },
        {
            'MetricName': 'VLLMRunningRequests',
            'Dimensions': dimensions,
            'Timestamp': timestamp,
            'Value': metrics['requests_running'],
            'Unit': 'Count',
            'StorageResolution': storage_resolution,
        },
        {
            'MetricName': 'VLLMWaitingRequests',
            'Dimensions': dimensions,
            'Timestamp': timestamp,
            'Value': metrics['requests_waiting'],
            'Unit': 'Count',
            'StorageResolution': storage_resolution,
        }
    ]
    
    try:
        response = cw_client.put_metric_data(
            Namespace=namespace,
            MetricData=metric_data
        )
        return True
    except Exception as e:
        print(f"Error sending metrics to CloudWatch: {e}")
        return False


def monitor_metrics(url: str, interval: int, cloudwatch_enabled: bool):
    """Monitor the metrics endpoint and display statistics at specified intervals."""
    previous_metrics = None
    start_time = time.time()
    
    # Set up CloudWatch if enabled
    cw_client = None
    cloudwatch_namespace = None
    cloudwatch_dimensions = []
    
    if cloudwatch_enabled:
        try:
            # Get CloudWatch configuration from environment variables
            cloudwatch_namespace = os.environ.get("CLOUDWATCH_NAMESPACE", "/aws/sagemaker/Endpoints")
            endpoint_name = os.environ.get("ENDPOINT_NAME", "UnknownEndpoint")
            variant_name = os.environ.get("VARIANT_NAME", "UnknownVariant")
            region_name = os.environ.get("AWS_REGION", "us-east-2")
            
            # Set up dimensions for CloudWatch metrics
            cloudwatch_dimensions = [
                {
                    'Name': 'EndpointName',
                    'Value': endpoint_name
                },
                {
                    'Name': 'VariantName',
                    'Value': variant_name
                }
            ]
            
            # Create CloudWatch client
            cw_client = boto3.client('cloudwatch', region_name=region_name)
            print(f"CloudWatch integration enabled. Namespace: {cloudwatch_namespace}")
            print(f"Dimensions: EndpointName={endpoint_name}, VariantName={variant_name}")
        except Exception as e:
            print(f"Error setting up CloudWatch: {e}")
            print("CloudWatch integration will be disabled")
            cloudwatch_enabled = False
    
    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        
        current_metrics = fetch_metrics(url)
        if not current_metrics:
            print(f"Waiting for valid metrics response... ({time.strftime('%H:%M:%S')})")
            time.sleep(interval)
            continue
        
        if previous_metrics:
            # Calculate metrics differences for this interval
            metrics_diff = {
                'prompt_tokens_diff': current_metrics["prompt_tokens"] - previous_metrics["prompt_tokens"],
                'gen_tokens_diff': current_metrics["generation_tokens"] - previous_metrics["generation_tokens"],
                'requests_diff': current_metrics["requests_success"]["total"] - previous_metrics["requests_success"]["total"]
            }
            
            # Calculate rates
            metrics_diff['total_tokens_diff'] = metrics_diff['prompt_tokens_diff'] + metrics_diff['gen_tokens_diff']
            metrics_diff['tokens_per_sec'] = metrics_diff['total_tokens_diff'] / interval
            metrics_diff['requests_per_sec'] = metrics_diff['requests_diff'] / interval
            
            # Format current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Print current statistics
            print(f"\n===== Stats at {timestamp} =====")
            print(f"Model: {current_metrics['model_name']}")
            print(f"Tokens/sec: {metrics_diff['tokens_per_sec']:.2f} (prompt: {metrics_diff['prompt_tokens_diff']:.0f}, generation: {metrics_diff['gen_tokens_diff']:.0f})")
            print(f"Requests/sec: {metrics_diff['requests_per_sec']:.2f}")
            print(f"Current running requests: {current_metrics['requests_running']}")
            print(f"Waiting requests: {current_metrics['requests_waiting']}")
            print(f"GPU cache usage: {current_metrics['gpu_cache_usage']*100:.2f}%")
            print(f"Total processed tokens: {current_metrics['prompt_tokens'] + current_metrics['generation_tokens']:.0f}")
            print(f"Total completed requests: {current_metrics['requests_success']['total']:.0f}")
            print(f"Running time: {int(elapsed // 60):02d}:{int(elapsed % 60):02d}")
            
            # Send metrics to CloudWatch if enabled
            if cloudwatch_enabled and cw_client:
                cw_success = send_to_cloudwatch(
                    current_metrics, 
                    metrics_diff,
                    cw_client,
                    cloudwatch_namespace, 
                    cloudwatch_dimensions,
                    interval=interval,
                )
                if cw_success:
                    print("✓ Metrics sent to CloudWatch:")
                    print("  - VLLMTokensPerSecond: {:.2f}".format(metrics_diff['tokens_per_sec']))
                    print("  - VLLMRequestsPerSecond: {:.2f}".format(metrics_diff['requests_per_sec']))
                    print("  - VLLMRunningRequests: {:.0f}".format(current_metrics['requests_running']))
                    print("  - VLLMWaitingRequests: {:.0f}".format(current_metrics['requests_waiting']))
            
        previous_metrics = current_metrics
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor vLLM metrics HTTP endpoint')
    parser.add_argument('--url', '-u', type=str, default='http://127.0.0.1:8080/metrics',
                        help='URL of the vLLM metrics endpoint')
    parser.add_argument('--interval', '-i', type=int, default=5,
                        help='Monitoring interval in seconds')
    parser.add_argument('--cloudwatch', '-c', action='store_true',
                        help='Enable CloudWatch integration')
    
    args = parser.parse_args()
    
    print(f"Starting metrics monitor with {args.interval} second intervals")
    print(f"Monitoring URL: {args.url}")
    if args.cloudwatch:
        print("CloudWatch integration enabled")
    print("Press Ctrl+C to exit")
    
    try:
        monitor_metrics(args.url, args.interval, args.cloudwatch)
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
