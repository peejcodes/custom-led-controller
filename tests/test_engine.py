from custom_led_controller.engine import FrameRenderer
from custom_led_controller.runtime import default_project


def test_renderer_returns_controller_frames():
    project = default_project()
    renderer = FrameRenderer()
    frames = renderer.render_project(project, seconds=1.23)
    assert len(frames) == len(project.controllers)
    assert frames[0].outputs
    assert all(len(output.colors) > 0 for output in frames[0].outputs)


def test_renderer_flattens_rgb_bytes():
    project = default_project()
    renderer = FrameRenderer()
    frame = renderer.render_project(project, seconds=0.5)[0]
    payloads = renderer.flatten_bytes(frame)
    first_output = frame.outputs[0]
    assert len(payloads[first_output.output_id]) == len(first_output.colors) * 3
