import pytest
from pydantic import ValidationError

from custom_led_controller.models import ControllerConfig, OutputConfig, ProjectConfig, SegmentConfig


def test_duplicate_outputs_rejected():
    with pytest.raises(ValidationError):
        ControllerConfig(
            id="c1",
            name="Test",
            outputs=[
                OutputConfig(id="o1", name="A", pin=1, led_count=10),
                OutputConfig(id="o1", name="B", pin=2, led_count=10),
            ],
        )


def test_segment_bounds_rejected():
    controller = ControllerConfig(
        id="c1",
        name="Test",
        outputs=[OutputConfig(id="o1", name="A", pin=1, led_count=10)],
    )
    with pytest.raises(ValidationError):
        ProjectConfig(
            controllers=[controller],
            segments=[SegmentConfig(id="s1", name="Bad", controller_id="c1", output_id="o1", start=5, length=10)],
        )
