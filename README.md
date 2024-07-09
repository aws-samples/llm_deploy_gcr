# Deploy large language model using AWS service (GCR)  

This is a sample code to deploy large language model using AWS service (GCR) 

## Overview
You could use different AWS service to deploy large language model. 
- Amazon [Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html) is a fully managed service that makes high-performing foundation models (FMs) from leading AI startups and Amazon available for your use through a unified API. You can choose from a wide range of foundation models to find the model that is best suited for your use case. Amazon Bedrock also offers a broad set of capabilities to build generative AI applications with security, privacy, and responsible AI. Using Amazon Bedrock, you can easily experiment with and evaluate top foundation models for your use cases, privately customize them with your data using techniques such as fine-tuning and Retrieval Augmented Generation (RAG), and build agents that execute tasks using your enterprise systems and data sources.

- Amazon [SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html) is a fully managed machine learning (ML) service. With SageMaker, you can store and share your data without having to build and manage your own servers. This gives you or your organizations more time to collaboratively build and develop your ML workflow, and do it sooner. SageMaker provides managed ML algorithms to run efficiently against extremely large data in a distributed environment. With built-in support for bring-your-own-algorithms and frameworks, SageMaker offers flexible distributed training options that adjust to your specific workflows. Within a few steps, you can deploy a model into a secure and scalable environment from the SageMaker console.

## Prerequisites  
- AWS account  
- AWS SageMaker Notebook instance

## How to use  
- Create a SageMaker Notebook instance with the following configuration:  
  - Instance type: ml.t3.medium (1 vCPU, 2 GiB memory)  
  - Volume size: 100 GiB
  - IAM role: SageMakerFullAccess
  - Click "Create Notebook Instance" button to create a SageMaker Notebook instance.
  - Click "Open JupyterLab" button to open a SageMaker Notebook instance.
  - Git repositories: https://github.com/aws-samples/llm_deploy_gcr.git
  - Click "Git Clone" button to clone the repository.

- cd llm_deploy_gcr/
- Chose Service which you want to use.
- cd sagemaker/ or cd bedrock/
- Run the code in Jupyter Notebook.


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

