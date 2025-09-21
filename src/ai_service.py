import boto3
import json
import os

class AIService:
    def __init__(self, region_name="us-east-1"):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region_name,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        self.llm_model = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def _invoke_model(self, model_id: str, payload: dict) -> dict:
        """Core method to invoke any Bedrock model"""
        try:
            request = json.dumps(payload)
            response = self.client.invoke_model(modelId=model_id, body=request)
            return json.loads(response["body"].read())
        except Exception as e:
            print(f"Error invoking model {model_id}: {e}")
            return {}
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using Claude model"""
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        response = self._invoke_model(self.llm_model, payload)
        
        if "content" in response:
            return response["content"][0]["text"]
        return ""