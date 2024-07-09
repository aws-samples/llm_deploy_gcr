# 使用AWS服务(GCR)部署大型语言模型

这是一个使用AWS服务(GCR)部署大型语言模型的示例代码

## 概述
您可以使用不同的AWS服务来部署大型语言模型。
- Amazon [Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html) 是一项全面托管服务，可通过统一API让您使用来自领先AI初创公司和Amazon的高性能基础模型(FM)。您可以从广泛的基础模型中进行选择，以找到最适合您用例的模型。Amazon Bedrock还提供了一套广泛的功能，可以在安全、隐私和负责任AI的前提下构建生成式AI应用程序。使用Amazon Bedrock，您可以轻松地针对您的用例试验和评估顶级基础模型，使用诸如微调和检索增强生成(RAG)等技术对它们进行私有定制，并构建使用您的企业系统和数据源执行任务的智能体。

- Amazon [SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html) 是一项全面托管的机器学习(ML)服务。使用SageMaker，您可以存储和共享数据，而无需构建和管理自己的服务器。这为您或您的组织提供了更多时间来协作构建和开发ML工作流程，并更快地完成。SageMaker提供托管ML算法，可在分布式环境中高效运行极大数据。凭借对自带算法和框架的内置支持，SageMaker提供了灵活的分布式训练选项，可调整到您的特定工作流程。只需几个步骤，您就可以从SageMaker控制台将模型部署到安全且可扩展的环境中。

## 先决条件
- AWS账户
- AWS SageMaker 笔记本实例

## 如何使用
- 使用以下配置创建 SageMaker 笔记本实例:
  - 实例类型：ml.m5.xlarge(4 vCPU，16 GiB内存)
  - 卷大小：100 GiB
  - IAM角色：SageMakerFullAccess
  - 单击“创建笔记本实例”按钮创建SageMaker笔记本实例。
  - 单击“打开JupyterLab”按钮打开SageMaker笔记本实例。
  - Git存储库： https://github.com/aws-samples/llm_deploy_gcr.git
  - 单击“Git克隆”按钮克隆存储库。

- cd llm_deploy_gcr/
- 选择要使用的服务。
- cd sagemaker/ 或 cd bedrock/
- 在 Jupyter Notebook 中运行代码。

## 安全

有关更多信息，请参阅[CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications)。

## 许可证

此库根据MIT-0许可证授权。请参阅LICENSE文件。