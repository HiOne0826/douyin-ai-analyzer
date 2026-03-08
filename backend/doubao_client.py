"""
火山引擎豆包API客户端
使用ARK API Key直接调用，无需签名
"""
import os
import json
import time
from typing import Dict, Any, List, Optional, Generator
from dotenv import load_dotenv
import requests

load_dotenv()

class DoubaoClient:
    def __init__(self):
        self.api_key = os.getenv("ARK_API_KEY")
        self.region = os.getenv("VOLC_REGION", "cn-beijing")
        self.model = os.getenv("DOUBAO_MODEL", "doubao-seed-2-0-lite-260215")
        self.endpoint_id = os.getenv("ENDPOINT_ID", "ep-20260307195004-rtvdc")
        self.timeout = 60
        self.api_host = f"ark.cn-beijing.volces.com"
        self.api_path = f"/api/v3/chat/completions"

    def _construct_message(self, prompt: str, image_base64_list: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """构造请求消息，支持多图"""
        messages = []

        # 系统提示词
        system_prompt = """你是专业的社交媒体内容分析师，深耕抖音和小红书平台，精通内容算法、用户心理和爆款逻辑。
你的分析要专业、精准、可落地，避免空泛的套话。输出格式使用Markdown，结构清晰，重点突出。"""

        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # 用户消息
        if image_base64_list and len(image_base64_list) > 0:
            # 多模态消息
            content = [{"type": "text", "text": prompt}]
            for img_b64 in image_base64_list:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img_b64}
                })
        else:
            # 纯文本消息
            content = prompt

        messages.append({
            "role": "user",
            "content": content
        })

        return messages

    def chat_stream(self, prompt: str, image_base64_list: Optional[List[str]] = None) -> Generator[str, None, None]:
        """流式调用豆包API"""
        if not self.api_key:
            yield "⚠️ 豆包API未配置，请先在.env文件中配置ARK_API_KEY\n"
            return
        
        try:
            messages = self._construct_message(prompt, image_base64_list)

            body = json.dumps({
                "model": self.model,
                "messages": messages,
                "stream": True,
            })
            
            # 构造请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            
            # 发送请求
            url = f"https://{self.api_host}{self.api_path}"
            response = requests.post(
                url,
                headers=headers,
                data=body,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            json_data = json.loads(data)
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                delta = json_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield f"❌ 调用豆包API失败: {str(e)}\n"
            # 打印详细错误信息
            import traceback
            traceback.print_exc()

    def chat(self, prompt: str, image_base64_list: Optional[List[str]] = None) -> str:
        """非流式调用豆包API"""
        if not self.api_key:
            return "⚠️ 豆包API未配置，请先在.env文件中配置ARK_API_KEY"
        
        try:
            messages = self._construct_message(prompt, image_base64_list)
            
            body = json.dumps({
                "model": self.model,
                "messages": messages,
                "stream": False,
                "reasoning_effort": "medium"
            })
            
            # 构造请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            
            # 发送请求
            url = f"https://{self.api_host}{self.api_path}"
            response = requests.post(
                url,
                headers=headers,
                data=body,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return "❌ 豆包API返回结果异常"
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ 调用豆包API失败: {str(e)}"

# 单例实例
doubao_client = DoubaoClient()
