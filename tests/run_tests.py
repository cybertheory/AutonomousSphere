#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import time

def run_tests(test_type=None, verbose=False):
    """Run the specified tests"""
    # Determine the pytest command
    pytest_cmd = ["pytest"]
    
    # Add verbosity if requested
    if verbose:
        pytest_cmd.append("-v")
    
    # Add test selection based on type
    if test_type == "unit":
        pytest_cmd.append("tests/unit/")
    elif test_type == "integration":
        pytest_cmd.append("tests/integration/")
    elif test_type == "e2e":
        pytest_cmd.append("tests/e2e/")
    else:
        # Run all tests if no type specified
        pytest_cmd.append("tests/")
    
    # Add coverage reporting
    pytest_cmd.extend(["--cov=AutonomousSphere", "--cov-report=term", "--cov-report=html:tests/coverage"])
    
    # Run the tests
    result = subprocess.run(pytest_cmd)
    return result.returncode

def check_docker_status():
    """Check if Docker containers are running"""
    result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
    
    # Check for required containers
    required_containers = ["postgres", "synapse", "autonomoussphere"]
    running_containers = result.stdout.lower()
    
    missing_containers = []
    for container in required_containers:
        if container not in running_containers:
            missing_containers.append(container)
    
    return missing_containers

def start_docker_environment():
    """Start the Docker environment if not already running"""
    missing_containers = check_docker_status()
    
    if missing_containers:
        print(f"Starting Docker containers: {', '.join(missing_containers)}")
        subprocess.run(["docker-compose", "up", "-d"])
        
        # Wait for containers to be ready
        print("Waiting for containers to be ready...")
        time.sleep(10)  # Give containers some time to start
        
        # Check again
        still_missing = check_docker_status()
        if still_missing:
            print(f"Warning: Some containers may not have started: {', '.join(still_missing)}")
            return False
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AutonomousSphere tests")
    parser.add_argument("--type", choices=["unit", "integration", "e2e"], help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-docker", action="store_true", help="Skip Docker environment check/start")
    
    args = parser.parse_args()
    
    # Check/start Docker environment if needed for integration or e2e tests
    if not args.no_docker and (args.type in ["integration", "e2e"] or args.type is None):
        if not start_docker_environment():
            print("Warning: Docker environment may not be fully ready")
    
    # Run the tests
    exit_code = run_tests(args.type, args.verbose)
    sys.exit(exit_code)