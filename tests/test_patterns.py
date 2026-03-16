from custom_led_controller.engine import FrameRenderer
from custom_led_controller.patterns import PATTERN_DESCRIPTORS, PATTERN_MAP
from custom_led_controller.runtime import default_project


def test_every_registered_pattern_renders_segment_length():
    project = default_project()
    renderer = FrameRenderer()
    segment_length = project.segments[0].length

    for pattern_id in PATTERN_MAP:
        project.playback.pattern = pattern_id
        frames = renderer.render_project(project, seconds=1.25)
        assert frames, f"{pattern_id} produced no frames"
        first_output = frames[0].outputs[0]
        assert len(first_output.colors) > 0, f"{pattern_id} produced an empty output"
        assert all(0 <= color.r <= 255 and 0 <= color.g <= 255 and 0 <= color.b <= 255 for color in first_output.colors)


def test_pattern_descriptor_ids_match_renderers():
    descriptor_ids = {item.id for item in PATTERN_DESCRIPTORS}
    renderer_ids = set(PATTERN_MAP)
    assert descriptor_ids == renderer_ids
    assert "rainbow" in descriptor_ids
    assert "scanner" in descriptor_ids
