# vLLM SageMaker Deployment

This project contains scripts and configurations for deploying and testing a vLLM (Vector Language Model) endpoint on AWS SageMaker.

## Project Structure

- `app/`: Directory containing the `serve` file
- `dockerfile`: Docker configuration for the vLLM endpoint
- `build_and_push.sh`: Script to build and push the Docker image
- `deploy_and_test.ipynb`: Jupyter notebook for deployment and testing

## Build docker image

Build and push the Docker image:

```
./build_and_push.sh
```

## Deployment and Testing

For a more interactive deployment and testing process, you can use the `deploy_and_test.ipynb` Jupyter notebook.
