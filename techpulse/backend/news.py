from typing import Dict, Any, List

class NewsManager:
    # Curated real-world technology updates matching categories: AI, Programming, Cybersecurity
    _news_data: Dict[str, Dict[str, str]] = {
        "ai": {
            "topic": "Meta's Llama 3.1 405B Release",
            "what_happened": "Meta released their flagship open-source AI model, Llama 3.1 405B, rivaling top commercial closed models in reasoning and coding.",
            "why_it_matters": "It allows developers to run, customize, and distill state-of-the-art AI models locally or in private clouds, lowering the cost of advanced intelligence."
        },
        "programming": {
            "topic": "Python 3.13 Experimental GIL Removal",
            "what_happened": "Python 3.13 introduced an experimental build that runs without the Global Interpreter Lock, enabling true multi-core parallel execution.",
            "why_it_matters": "This allows CPU-bound Python programs to run significantly faster on modern multi-core processors without resorting to complex multi-process workarounds."
        },
        "cybersecurity": {
            "topic": "CrowdStrike Global IT Outage",
            "what_happened": "A faulty update to CrowdStrike's Falcon Sensor security software triggered a blue screen crash loop on millions of Windows systems worldwide, halting airlines, banks, and healthcare.",
            "why_it_matters": "It demonstrates the fragility of kernel-level third-party updates and the critical importance of phased rollouts and validation pipelines in global supply chains."
        }
    }

    _fallback_briefing: str = (
        "I don't have access to a verified current update right now, so I'll give you a general technology insight instead."
    )

    @classmethod
    def get_all_news(cls) -> Dict[str, Dict[str, str]]:
        """Returns structured news items for all categories."""
        return cls._news_data

    @classmethod
    def get_news_by_category(cls, category: str) -> Dict[str, str]:
        """Returns news item for a specific category (ai, programming, cybersecurity)."""
        return cls._news_data.get(category.lower(), {})

    @classmethod
    def get_compiled_briefing(cls, use_fallback: bool = False) -> str:
        """
        Compiles a natural sounding technology update briefing.
        If use_fallback is True, returns the exact fallback message requested by specifications.
        """
        if use_fallback:
            return cls._fallback_briefing

        briefing_parts = []
        for category, info in cls._news_data.items():
            cat_name = "Artificial Intelligence" if category == "ai" else category.capitalize()
            text = (
                f"Under {cat_name}: the topic is {info['topic']}. "
                f"Specifically, {info['what_happened']} "
                f"This matters because {info['why_it_matters']}"
            )
            briefing_parts.append(text)

        return " ".join(briefing_parts)
