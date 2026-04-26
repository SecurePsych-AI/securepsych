import logging
import os
import yaml

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


async def run_simplify_chain(text: str, template: str) -> str:
    cfg = _load_config()["jargon"]
    llm = ChatOllama(model=cfg["model"], base_url=cfg["ollama_base_url"])
    prompt = PromptTemplate(input_variables=["text"], template=template)
    chain = prompt | llm | StrOutputParser()
    logger.info("[jargon] Invoking simplify chain")
    result = await chain.ainvoke({"text": text})
    logger.info("[jargon] Chain complete — output length: %d chars", len(result))
    return result
