"""Реестр проверок L1: id → run(plugin, ctx, manifest) -> list[Finding].

Каждая задача плана добавляет сюда свою строку; порядок запуска задаёт
model.CHECK_IDS, а не этот словарь.
"""
from . import skill_links, skill_snippets

REGISTRY = {
    "skill-links": skill_links.run,
    "skill-snippets": skill_snippets.run,
}
