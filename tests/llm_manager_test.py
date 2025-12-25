import logging
from app.services.llms.manager import LLMManager

logging.basicConfig(level=logging.INFO)

def test_llm_auto_mode():
    llm_manager = LLMManager(temperature=0.1)

    llm = llm_manager.get_llm()
    response = llm.invoke("Halo, jawab singkat saja: siapa kamu?")

    print("Response:", response.content)
    assert response.content is not None


if __name__ == "__main__":
    test_llm_auto_mode()
