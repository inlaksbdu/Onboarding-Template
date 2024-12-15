from typing import Any, Dict, Type, TYPE_CHECKING, List, Union
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage

from .prompt import SYSTEM_PROMPT
from .schema import DocumentInfo, IDDocument
from library.utils import encode_image_to_base64

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


class DocumentOCRProcessor:
    def __init__(
        self, llm: "BaseChatModel", output_schema: Type[BaseModel] = IDDocument
    ):
        self.llm = llm.with_structured_output(output_schema)
        self.output_schema = output_schema

    async def process_images(self, images: List[Union[str, bytes]]) -> BaseModel:
        human_messages: List[Dict[str, Any]] = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_image_to_base64(img)}"
                },
            }
            for img in images
        ]

        return await self.llm.ainvoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_messages)]  # type: ignore
        )
