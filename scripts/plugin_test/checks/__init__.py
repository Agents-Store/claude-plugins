"""Реестр проверок L1: id → run(plugin, ctx, manifest) -> list[Finding].

Каждая задача плана добавляет сюда свою строку; порядок запуска задаёт
model.CHECK_IDS, а не этот словарь.
"""
from . import hook_fixtures, mcp_list, mcp_names, skill_budget, skill_links, skill_snippets

REGISTRY = {
    "skill-links": skill_links.run,
    "skill-snippets": skill_snippets.run,
    "skill-budget": skill_budget.run,
    "mcp-names": mcp_names.run,
    "mcp-list": mcp_list.run,
    "hook-fixtures": hook_fixtures.run,
}
