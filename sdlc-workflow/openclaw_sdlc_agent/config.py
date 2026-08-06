import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class SDLCConfig:
    """OpenClaw SDLC Agent 全局运行时配置"""
    
    # OpenAI 相关配置
    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    openai_api_base: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    model_name: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o")
    )
    temperature: float = 0.1

    # SDLC 业务与容错配置
    max_consistency_retries: int = 3
    default_export_dir: str = "./generated_project"

    @classmethod
    def from_dict(cls, config_dict: Optional[Dict[str, Any]] = None) -> "SDLCConfig":
        """从字典对象动态创建/覆盖配置（用于 OpenClaw 框架注入参数）"""
        if not config_dict:
            return cls()
            
        return cls(
            openai_api_key=config_dict.get("openai_api_key") or os.getenv("OPENAI_API_KEY", ""),
            openai_api_base=config_dict.get("openai_api_base") or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
            model_name=config_dict.get("model_name") or os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=float(config_dict.get("temperature", 0.1)),
            max_consistency_retries=int(config_dict.get("max_consistency_retries", 3)),
            default_export_dir=config_dict.get("default_export_dir", "./generated_project"),
        )

# 单例全局默认配置
settings = SDLCConfig()
