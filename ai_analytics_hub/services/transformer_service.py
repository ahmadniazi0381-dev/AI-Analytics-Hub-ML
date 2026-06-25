from __future__ import annotations

from functools import lru_cache

from flask import current_app

from ai_analytics_hub.core.exceptions import DependencyNotInstalledError


QA_MODEL = "deepset/roberta-base-squad2"
TEXT_MODEL = "gpt2"
NER_MODEL = "dbmdz/bert-large-cased-finetuned-conll03-english"


def answer_question(*, context: str, question: str) -> dict:
    pipeline = _get_qa_pipeline()
    result = pipeline(question=question, context=context)
    return {
        "answer": result["answer"],
        "score": round(float(result["score"]), 4),
        "model_name": QA_MODEL,
    }


def generate_text(*, prompt: str, max_new_tokens: int, temperature: float) -> dict:
    pipeline = _get_text_generation_pipeline()
    result = pipeline(
        prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=True,
        pad_token_id=pipeline.tokenizer.eos_token_id,
    )
    generated_text = result[0]["generated_text"]
    return {
        "generated_text": generated_text,
        "model_name": TEXT_MODEL,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
    }


def extract_entities(*, text: str) -> dict:
    pipeline = _get_ner_pipeline()
    entities = pipeline(text)
    return {
        "entities": [
            {
                "entity": item.get("word"),
                "label": item.get("entity_group"),
                "score": round(float(item.get("score", 0.0)), 4),
            }
            for item in entities
        ],
        "model_name": NER_MODEL,
    }


@lru_cache(maxsize=1)
def _get_qa_pipeline():
    return _build_pipeline("question-answering", QA_MODEL)


@lru_cache(maxsize=1)
def _get_text_generation_pipeline():
    return _build_pipeline("text-generation", TEXT_MODEL)


@lru_cache(maxsize=1)
def _get_ner_pipeline():
    return _build_pipeline("token-classification", NER_MODEL, aggregation_strategy="simple")


def _build_pipeline(task: str, model_name: str, **kwargs):
    try:
        from transformers import pipeline
    except ImportError as error:
        raise DependencyNotInstalledError(
            "Transformer dependencies are not installed. Run 'pip install -e .[genai]'."
        ) from error

    cache_dir = current_app.config["MODEL_CACHE_DIR"]
    return pipeline(task=task, model=model_name, tokenizer=model_name, cache_dir=cache_dir, **kwargs)
