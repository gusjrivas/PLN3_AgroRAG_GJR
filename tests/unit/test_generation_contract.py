def test_generation_prompts_separate_factual_support_from_missing_referents() -> None:
    from agro_rag.infrastructure.generation_contract import PROMPTS

    assert "pregunta factual" in PROMPTS["researcher"]
    assert "referente" in PROMPTS["researcher"]
    assert "pregunta factual" in PROMPTS["verifier"]
    assert "referente" in PROMPTS["verifier"]
