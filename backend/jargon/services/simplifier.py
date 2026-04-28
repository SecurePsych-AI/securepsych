import logging
import os

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

_OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
_OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]


async def run_simplify_chain(text: str, template: str) -> str:
    llm = ChatOllama(model=_OLLAMA_MODEL, base_url=_OLLAMA_BASE_URL)
    prompt = PromptTemplate(input_variables=["text"], template=template)
    chain = prompt | llm | StrOutputParser()
    logger.info("[jargon] Invoking simplify chain")
    result = await chain.ainvoke({"text": text})
    logger.info("[jargon] Chain complete — output length: %d chars", len(result))
    return result
