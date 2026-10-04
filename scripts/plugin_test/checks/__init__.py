"""Реестр проверок L1: id → run(plugin, ctx, manifest) -> list[Finding].

Каждая задача плана добавляет сюда свою строку; порядок запуска задаёт
model.CHECK_IDS, а не этот словарь.
"""
REGISTRY = {}
