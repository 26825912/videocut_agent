"""
Simple FunASR Test - Avoiding Unicode Issues
Direct test of FunASR subtitle generation functionality
"""

import sys
import os
from pathlib import Path

# Setup paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "tools"))

def test_funasr_basic():
    """Test basic FunASR transcription"""
    print("=== Testing FunASR Basic Transcription ===")

    try:
        from tools.asr_base import get_transcriber

        # Check test audio
        audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"
        if not os.path.exists(audio_path):
            print(f"SKIP: Test audio not found - {audio_path}")
            return None

        print(f"Using test audio: {audio_path}")
        file_size = os.path.getsize(audio_path)
        print(f"Audio size: {file_size} bytes")

        # Create transcriber
        transcriber = get_transcriber(provider="funasr", language="zh-cn")
        print("OK: FunASR transcriber created")

        # Transcribe audio
        print("Starting transcription...")
        segments = transcriber.file_to_text(audio_path)

        if segments:
            print(f"SUCCESS: Found {len(segments)} segments")

            # Show first few segments
            print("Transcription results:")
            for i, seg in enumerate(segments[:3]):
                start = seg.get('start_time', 0)
                end = seg.get('end_time', 0)
                text = seg.get('text', '')
                print(f"  {i+1}: [{start:.2f}s-{end:.2f}s] {text}")

            if len(segments) > 3:
                print(f"  ... and {len(segments) - 3} more segments")

            return segments
        else:
            print("FAIL: No transcription results")
            return None

    except Exception as e:
        print(f"ERROR: {e}")
        return None

def create_srt_subtitle(segments, output_path):
    """Create SRT subtitle file from segments"""
    try:
        srt_content = ""
        for i, segment in enumerate(segments, 1):
            start_time = format_srt_time(segment.get('start_time', 0))
            end_time = format_srt_time(segment.get('end_time', 0))
            text = segment.get('text', '')

            srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"

        # Save file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        print(f"Subtitle saved: {output_path}")

        # Show preview
        print("Content preview:")
        print("-" * 40)
        preview = srt_content[:200] + "..." if len(srt_content) > 200 else srt_content
        print(preview)
        print("-" * 40)

        return output_path

    except Exception as e:
        print(f"ERROR creating subtitle: {e}")
        return None

def format_srt_time(seconds):
    """Format seconds to SRT time format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def test_azure_comparison():
    """Compare with Azure if available"""
    print("\n=== Testing Azure Comparison ===")

    audio_path = "models/funasr/paraformer_zh/example/asr_example.wav"

    try:
        from tools.asr_base import get_transcriber

        # Test Azure
        azure_transcriber = get_transcriber(provider="azure", language="zh-cn")
        azure_segments = azure_transcriber.file_to_text(audio_path)

        if azure_segments:
            print("Azure transcription:")
            azure_text = " ".join([seg.get('text', '') for seg in azure_segments])
            print(f"  Result: {azure_text}")
            print(f"  Segments: {len(azure_segments)}")
        else:
            print("Azure transcription failed")

    except Exception as e:
        print(f"Azure test failed: {e}")

def main():
    """Main test function"""
    print("FunASR Subtitle Generation Test")
    print("=" * 50)

    # Test basic transcription
    segments = test_funasr_basic()

    if segments:
        # Create subtitle file
        output_dir = Path("data/result_video/subtitles")
        output_file = output_dir / "funasr_test.srt"

        subtitle_file = create_srt_subtitle(segments, output_file)

        if subtitle_file:
            print(f"\nSUCCESS: Subtitle generation completed")
            print(f"File: {subtitle_file}")

            # Test Azure comparison
            test_azure_comparison()

            print(f"\n" + "=" * 50)
            print("Test Results Summary:")
            print(f"- FunASR transcription: PASS ({len(segments)} segments)")
            print(f"- Subtitle file creation: PASS")
            print(f"- Output file: {subtitle_file}")
            print("\nFunASR subtitle generation is working correctly!")
        else:
            print("FAIL: Could not create subtitle file")
    else:
        print("FAIL: FunASR transcription failed")

if __name__ == "__main__":
    main()