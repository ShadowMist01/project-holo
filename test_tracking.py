"""Camera-free control-flow check, not a real OpenCV/MediaPipe inference test."""
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch


class StopAfterFrame(Exception):
    pass


def check_frame(hand_count):
    calls = []
    image = NS(shape=(480, 640, 3))
    rgb = object()
    landmarks = NS(landmark=[NS(x=0.25, y=0.5) for _ in range(21)])
    results = NS(multi_hand_landmarks=[landmarks] * hand_count or None)

    def capture(index):
        assert index == 0
        return NS(read=lambda: (True, image))

    def convert(frame, mode):
        assert frame is image and mode == 'BGR2RGB'
        calls.append('convert')
        return rgb

    def process(frame):
        assert frame is rgb
        calls.append('process')
        return results

    def circle(frame, center, radius, color, fill):
        assert frame is image
        assert (center, radius, color, fill) == ((160, 240), 25, (255, 0, 255), 'FILLED')
        calls.append('circle')

    def draw(frame, hand, connections):
        assert frame is image and hand is landmarks and connections == 'connections'
        calls.append('draw')

    def show(title, frame):
        assert title == 'Output' and frame is image
        calls.append('show')

    def stop(delay):
        assert delay == 1
        raise StopAfterFrame

    cv2 = NS(VideoCapture=capture, COLOR_BGR2RGB='BGR2RGB', cvtColor=convert,
             circle=circle, FILLED='FILLED', imshow=show, waitKey=stop)
    mp = NS(solutions=NS(hands=NS(Hands=lambda: NS(process=process),
                                 HAND_CONNECTIONS='connections'),
                         drawing_utils=NS(draw_landmarks=draw)))
    # Both imported camera/inference modules are replaced before main.py executes.
    with patch.dict(sys.modules, {'cv2': cv2, 'mediapipe': mp}):
        try:
            runpy.run_path(str(Path(__file__).with_name('main.py')), run_name='__main__')
        except StopAfterFrame:
            pass
        else:
            raise AssertionError('Expected one-frame stop')
    assert calls[:2] == ['convert', 'process'] and calls[-1] == 'show'
    assert calls.count('circle') == hand_count
    # Preserve and expose the historical nested drawing loop; do not conceal it.
    assert calls.count('draw') == 21 * hand_count


if __name__ == '__main__':
    for count in (0, 1, 2):
        check_frame(count)
    print('PASS: 3 substituted-module frame scenarios (0, 1, 2 hands); no camera or ML runtime used')
