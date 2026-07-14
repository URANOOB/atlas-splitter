"""Prompt determinista para los futuros motores multimodales."""

from __future__ import annotations


def build_grouping_prompt() -> str:
    """Devuelve las instrucciones JSON estables para el modelo semántico."""
    return """You are analyzing isolated texture-atlas pieces.

Each piece has an ID such as E001.

Group pieces only when they probably belong to the same original 3D object.
Pieces belonging to the same object may look different because they can represent roofs, walls, doors,
windows, sides, bottoms, clothing sections, limbs or other complementary surfaces.

Do not group pieces only because they have similar colors.
Use visual style, material, scale, edge patterns, complementary structure, atlas context and semantic compatibility.

Every piece ID must appear exactly once, either inside a group or in unassigned_piece_ids.

Use concise English object names in snake_case.
When the object cannot be identified, use unknown_object.

Return JSON only, with this schema:
{"groups":[{"name":"house","piece_ids":["E001"],"confidence":0.87}],"unassigned_piece_ids":["E002"]}"""


def build_candidate_analysis_prompt() -> str:
    """Instrucciones estrictas para clasificar sin autorizar acciones fuera de JSON."""
    return """Analyze the atlas, contact sheet and candidate crops. Return JSON only.
You may only describe candidates; never write files, execute commands or suggest paths.
Every candidate must appear once in candidates. Use stable candidate IDs exactly as supplied.
Schema: {"candidates":[{"candidate_id":"element_001","label":"roof","category":"architecture",
"object_group":"house_001","part_role":"roof","orientation":"front","confidence":0.91,
"related_candidates":["element_004"],"discard":false,"reason":"brief evidence"}]}"""
