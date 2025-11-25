import json
import numpy as np
import torch
import triton_python_backend_utils as pb_utils

from diffusers import StableDiffusionXLPipeline

from io import BytesIO
import base64


def encode_images(images):
    encoded_images = []
    for image in images:
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        img_str = base64.b64encode(buffer.getvalue())
        encoded_images.append(img_str.decode("utf8"))

    return encoded_images


class TritonPythonModel:

    def initialize(self, args):

        self.model_dir = args['model_repository']
        self.model_ver = args['model_version']

        device='cuda'

        # 載入模型
        self.pipe = StableDiffusionXLPipeline.from_single_file(
                    f'{self.model_dir}/{self.model_ver}/checkpoint/Illustrious-XL-v1.0.safetensors',
                    torch_dtype=torch.float16,
                    use_safetensors=True
                )

        self.pipe.to(device)
        

    def execute(self, requests):
        
        logger = pb_utils.Logger
        responses = []
        for request in requests:
            prompt = pb_utils.get_input_tensor_by_name(request, "prompt").as_numpy().item().decode("utf-8")
            
            print("开始生成图像...")
            prompt = "a photo of an astronaut riding a horse on mars"
            images = self.pipe(prompt, height=1024, width=1024).images
            print("✅ 图像生成完成")
            encoded_images = encode_images(images)

            responses.append(pb_utils.InferenceResponse([pb_utils.Tensor("generated_image", np.array(encoded_images).astype(object))]))
        
        return responses
