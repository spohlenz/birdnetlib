from birdnetlib import LargeRecording, Recording, IncompatibleAnalyzerError
from birdnetlib.analyzer import LargeRecordingAnalyzer, Analyzer
import pytest
from pprint import pprint
import os
import tempfile
import csv
import time
import json
import pydub
import librosa
import numpy as np
from birdnetlib.utils import read_audio_segments


LOG_FILE = "log.txt"


def log(text_to_append):
    pass
    # with open(LOG_FILE, "a") as file:
    #     file.write(text_to_append + "\n")


@pytest.mark.parametrize(
    "filepath,cls_type",
    [
        # ["test_files/22min/22m00s_48kHz_mono.wav", "large"],
        ["test_files/22min/22m00s_48kHz_mono.mp3", "large"],
        ["test_files/22min/22m00s_48kHz_mono.flac", "large"],
    ],
)
def test_large_with_analyzer(filepath, cls_type):
    # Process file with command line utility, then process with python library and ensure equal commandline_results.

    lon = -120.7463
    lat = 35.4244
    week_48 = 18
    min_conf = 0.25
    input_path = os.path.join(os.path.dirname(__file__), filepath)

    tf = tempfile.NamedTemporaryFile(suffix=".csv")
    output_path = tf.name

    # Process using python script as is.
    birdnet_analyzer_path = os.path.join(os.path.dirname(__file__), "BirdNET-Analyzer")

    cmd = f"python analyze.py --i '{input_path}' --o={output_path} --lat {lat} --lon {lon} --week {week_48} --min_conf {min_conf} --rtype=csv"
    print(cmd)
    os.system(f"cd {birdnet_analyzer_path}; {cmd}")

    with open(tf.name) as f:
        for line in f:
            print(line)

    with open(tf.name, newline="") as csvfile:
        # reader = csv.reader(csvfile, delimiter=";", quotechar="|")
        reader = csv.DictReader(csvfile)
        commandline_results = []
        for row in reader:
            commandline_results.append(
                {
                    "start_time": float(row["Start (s)"]),
                    "end_time": float(row["End (s)"]),
                    "common_name": row["Common name"],
                    "scientific_name": row["Scientific name"],
                    "confidence": float(row["Confidence"]),
                }
            )

    # pprint(commandline_results)
    assert len(commandline_results) > 0

    if cls_type == "normal":
        # Normal file method, for comparison and memory profiling.
        # This can be observed with top or a pytest memory profiler.
        bnl_start_time = time.time()
        analyzer = Analyzer()
        recording = Recording(
            analyzer,
            input_path,
            lat=lat,
            lon=lon,
            week_48=week_48,
            min_conf=min_conf,
        )
        recording.analyze()

        bnl_duration = time.time() - bnl_start_time

    else:
        # large file file method.
        bnl_start_time = time.time()
        analyzer = LargeRecordingAnalyzer()
        recording = LargeRecording(
            analyzer,
            input_path,
            lat=lat,
            lon=lon,
            week_48=week_48,
            min_conf=min_conf,
        )
        recording.analyze()
        bnl_duration = time.time() - bnl_start_time

    pprint(recording.detections)

    # Check that birdnetlib results match command line results.
    assert len(recording.detections) == len(commandline_results)
    assert (
        len(analyzer.custom_species_list) == 195
    )  # Check that this matches the number printed by the cli version.

    # Check that detection confidence is float.
    assert isinstance(recording.detections[0]["confidence"], float)

    # Check that detection confidence is float.
    assert isinstance(recording.detections[0]["confidence"], float)

    log("-" * 80)
    log(cls_type)
    log(filepath)
    log("-" * 80)

    log(
        json.dumps(
            {
                # "bna_duration_secs": cmd_line_duration,
                "bnl_duration_secs": bnl_duration,
            },
            indent=4,
        )
    )


def test_large_extractions():
    # TODO: These can not use the audio that's open on the recording. You'll need to reimplement the data reader.
    lon = -120.7463
    lat = 35.4244
    week_48 = 18
    min_conf = 0.25

    input_path = os.path.join(
        os.path.dirname(__file__), "test_files/22min/22m00s_48kHz_mono.flac"
    )

    analyzer = LargeRecordingAnalyzer()
    recording = LargeRecording(
        analyzer,
        input_path,
        lat=lat,
        lon=lon,
        week_48=week_48,
        min_conf=min_conf,
    )
    recording.analyze()

    with tempfile.TemporaryDirectory() as export_dir:
        recording.extract_detections_as_audio(
            directory=export_dir, format="wav", min_conf=0.7
        )

        # Check file list.
        files = os.listdir(export_dir)

        files.sort()

        expected_files = [
            "22m00s_48kHz_mono_1002s-1005s.wav",
            "22m00s_48kHz_mono_1122s-1125s.wav",
            "22m00s_48kHz_mono_1242s-1245s.wav",
            "22m00s_48kHz_mono_162s-165s.wav",
            "22m00s_48kHz_mono_282s-285s.wav",
            "22m00s_48kHz_mono_402s-405s.wav",
            "22m00s_48kHz_mono_42s-45s.wav",
            "22m00s_48kHz_mono_522s-525s.wav",
            "22m00s_48kHz_mono_642s-645s.wav",
            "22m00s_48kHz_mono_762s-765s.wav",
            "22m00s_48kHz_mono_882s-885s.wav",
        ]
        expected_files.sort()
        pprint(files)
        assert files == expected_files

        # Check that file format is wav, 48000, and correct size.
        audio = pydub.AudioSegment.from_wav(f"{export_dir}/{files[0]}")
        assert audio.frame_rate == 48000
        assert audio.duration_seconds == 3.0

    with tempfile.TemporaryDirectory() as export_dir:
        recording.extract_detections_as_spectrogram(
            directory=export_dir,
            format="jpg",
            min_conf=0.7,
            padding_secs=2,
        )

        # Check file list.
        files = os.listdir(export_dir)

        pprint(files)

        files.sort()
        expected_files = [
            "22m00s_48kHz_mono_1240s-1247s.jpg",
            "22m00s_48kHz_mono_280s-287s.jpg",
            "22m00s_48kHz_mono_1120s-1127s.jpg",
            "22m00s_48kHz_mono_1000s-1007s.jpg",
            "22m00s_48kHz_mono_760s-767s.jpg",
            "22m00s_48kHz_mono_400s-407s.jpg",
            "22m00s_48kHz_mono_40s-47s.jpg",
            "22m00s_48kHz_mono_520s-527s.jpg",
            "22m00s_48kHz_mono_880s-887s.jpg",
            "22m00s_48kHz_mono_640s-647s.jpg",
            "22m00s_48kHz_mono_160s-167s.jpg",
        ]
        expected_files.sort()

        assert files == expected_files


def test_exceptions():
    # LargeRecordingAnalyzer and LargeRecording have to be used in conjunction.
    # Test that exceptions are thrown if not used correctly.

    lon = -120.7463
    lat = 35.4244
    week_48 = 18
    min_conf = 0.25

    input_path = os.path.join(os.path.dirname(__file__), "test_files/soundscape.wav")

    with pytest.raises(IncompatibleAnalyzerError) as exc_info:
        analyzer = LargeRecordingAnalyzer()
        recording = Recording(
            analyzer,
            input_path,
            lat=lat,
            lon=lon,
            week_48=week_48,
            min_conf=min_conf,
        )
        recording.analyze()

    assert (
        str(exc_info.value)
        == "LargeRecordingAnalyzer can only be used with the LargeRecording class"
    )

    with pytest.raises(IncompatibleAnalyzerError) as exc_info:
        analyzer = Analyzer()
        recording = LargeRecording(
            analyzer,
            input_path,
            lat=lat,
            lon=lon,
            week_48=week_48,
            min_conf=min_conf,
        )
        recording.analyze()

    assert (
        str(exc_info.value) == "LargeRecording can only be used with the Analyzer class"
    )


# @pytest.mark.parametrize(
#     "filepath",
#     [
#         "test_files/22min/22m00s_32kHz_mono.flac",
#         # "test_files/22min/22m00s_48kHz_mono.wav",
#         # "test_files/edge_cases/NV017_20200331_120000.wav",
#     ],
# )
# def test_large_single(filepath):
#     # Process file with command line utility, then process with python library and ensure equal commandline_results.

#     lon = -120
#     lat = 39
#     week_48 = 12
#     min_conf = 0.25
#     input_path = os.path.join(os.path.dirname(__file__), filepath)

#     # large file file method.
#     analyzer = LargeRecordingAnalyzer()
#     recording = LargeRecording(
#         analyzer,
#         input_path,
#         lat=lat,
#         lon=lon,
#         week_48=week_48,
#         min_conf=min_conf,
#     )
#     recording.analyze()

#     # pprint(recording.detections)

#     with open("bnl_single.json", "w") as json_file:
#         json.dump(recording.detections, json_file, indent=4)

#     print("recording.detections", len(recording.detections))
#     assert (
#         len(analyzer.custom_species_list) == 148
#     )  # Check that this matches the number printed by the cli version.

#     # Check that detection confidence is float.
#     assert isinstance(recording.detections[0]["confidence"], float)

#     # Check that detection confidence is float.
#     assert isinstance(recording.detections[0]["confidence"], float)


@pytest.mark.parametrize(
    "filepath",
    [
        # "test_files/22min/22m00s_48kHz_mono.wav",
        "test_files/22min/22m00s_32kHz_mono.flac",
        "test_files/22min/22m00s_48kHz_mono.mp3",
        "test_files/22min/22m00s_48kHz_mono.flac",
    ],
)
def test_librosa(filepath):
    # Test the librosa segmenting reader.

    input_path = os.path.join(os.path.dirname(__file__), filepath)
    arr_0_5_a, sr = librosa.load(input_path, sr=48000, mono=True, offset=0, duration=5)
    arr_0_5_b, sr = librosa.load(input_path, sr=48000, mono=True, offset=0, duration=5)

    # Confirm assertion works.
    assert np.array_equal(arr_0_5_a, arr_0_5_b)

    # Use read_audio_segments
    segment_generator = read_audio_segments(
        input_path, chunk_duration=10, segment_duration=5
    )

    # Get the first two items only from the seg generator.
    results = []
    for item in segment_generator:
        results.append(item)
        if len(results) == 2:
            break

    arr_0_5_gen = results[0]["segment"]

    assert len(arr_0_5_a) == len(arr_0_5_gen)
    assert np.array_equal(arr_0_5_a[0:48000], arr_0_5_gen[0:48000])

    arr_5_10, sr = librosa.load(input_path, sr=48000, mono=True, offset=5, duration=5)
    arr_5_10_gen = results[1]["segment"]

    # Test for almost equality (accounting for tiny diff with 32k to 48k resampling diffs)
    is_almost_equal = are_audio_arrays_almost_equal(arr_5_10, arr_5_10_gen)
    assert is_almost_equal
    assert len(arr_5_10) == len(arr_5_10_gen)

    # Check that assertion works by forcing a 32000 file.
    arr_0_5_32k, sr = librosa.load(input_path, sr=32000, offset=0, duration=5)
    assert not np.array_equal(arr_0_5_a, arr_0_5_32k)


def are_audio_arrays_almost_equal(audio1, audio2, tolerance=0.0000000001):
    if audio1.shape != audio2.shape:
        return False

    # Calculate the Mean Squared Error (MSE) between the two audio arrays
    mse = np.mean((audio1 - audio2) ** 2)

    # Compare the MSE with a tolerance value
    return mse <= tolerance
