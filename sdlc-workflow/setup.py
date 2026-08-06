from setuptools import setup, find_packages

setup(
    name="openclaw-sdlc-agent",
    version="1.0.0",
    description="An enterprise SDLC Agent with MemorySaver checkpointer and Human-in-the-Loop approval for OpenClaw.",
    author="Dev Team",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.2.0",
        "langchain-openai>=0.1.0",
        "langchain-core>=0.2.0",
        "pydantic>=2.0",
        "pyyaml",
    ],
    entry_points={
        "openclaw.agents": [
            "sdlc_agent = openclaw_sdlc_agent.agent:SDLCOpenClawAgent",
        ],
    },
    python_requires=">=3.9",
)
