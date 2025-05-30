import os
import json
from typing import Optional, List

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

# LangChain и ваши импорты
from langchain_community.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Класс для этапа "сырое" -> "строка"
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser

# Ваши Pydantic-модели
class Person(BaseModel):
    name: str
    age: int
    occupation: str
    hair_color: Optional[str] = Field(
        default=None, description="The color of the person's hair if known"
    )

class People(BaseModel):
    people: List[Person]


# -----------------------------
# Глобальные объекты:
# - Модель/LLM
# - Цепочка (chain)
# -----------------------------
app = FastAPI()

# Эти переменные будут доступны из любой части кода после инициализации
llm = None
chain = None


def initialize_llm(model_path: str = "./models/Llama-3.2-3B-Instruct-Q8_0.gguf"):
    """
    Инициализация LlamaCpp модели и всего необходимого для цепочки.
    Возвращает (llm, chain).
    """
    # Проверка на существование файла модели (при желании можно убрать)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Файл модели не найден: {model_path}")

    print("Загрузка модели...", model_path)
    callbacks = [StreamingStdOutCallbackHandler()]
    stop_sequences = ["<|eot_id|>", "<|end_of_text|>"]

    _llm = LlamaCpp(
        model_path=model_path,
        temperature=0.1,
        max_tokens=512,
        n_ctx=1024,
        n_batch=512,
        callbacks=callbacks,
        use_mlock=True,
        verbose=False,
        seed=42,
        stop=stop_sequences,
        top_p=0.9,
        top_k=40,
        repeat_penalty=1.1,
    )
    print("Модель загружена!")

    # Настраиваем парсер
    parser = PydanticOutputParser(pydantic_object=People)

    # Шаблон для PromptTemplate
    prompt_template = """
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert assistant tasked with extracting information about people from text and formatting it strictly as a JSON object.
Only extract the requested fields: name, age, and occupation. Include hair_color if mentioned. Ignore other details like cars.
Your response MUST be ONLY the JSON object conforming to the schema below, enclosed in ```json ``` tags. Do not include any other text before or after the JSON block.
{format_instructions}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Extract information about the people described in the following text:

Text:
{text_input}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```json
"""
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["text_input"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    # Строим chain
    _chain = prompt | _llm | StrOutputParser() | parser
    return _llm, _chain


@app.on_event("startup")
def startup_event():
    """
    Хук FastAPI, который вызывается один раз при старте приложения.
    Здесь загружаем модель и готовим глобальную chain.
    """
    global llm, chain
    model_path = os.getenv("LLM_MODEL_PATH", "./models/Llama-3.2-3B-Instruct-Q8_0.gguf")
    llm, chain = initialize_llm(model_path=model_path)


@app.post("/classify")
async def classify_text(request: Request):
    """
    Основной эндпоинт, куда Rhasspy или любой другой клиент
    может послать POST-запрос с текстом для классификации/извлечения информации.

    Формат входных данных (JSON):
    {
       "text_input": "Некоторый текст с описанием людей"
    }

    Формат ответа (JSON), например:
    {
        "people": [
            {"name": "John", "age": 30, "occupation": "software engineer", "hair_color": "brown"},
            {"name": "Anna", "age": 25, "occupation": "data analyst", "hair_color": null}
        ]
    }
    """
    global chain
    data = await request.json()
    text_input = data.get("text_input", "")

    # Запускаем нашу chain
    try:
        result_obj = chain.invoke({"text_input": text_input})
        # result_obj - это Pydantic-объект People
        # Возвращаем его в виде обычного словаря (или JSON)
        return result_obj.model_dump()
    except Exception as e:
        # Если что-то пошло не так
        return {"error": str(e)}


# Если хотим запускать напрямую, пишем:
# python rhasspy_llm_service.py
# И он поднимется на порту 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
