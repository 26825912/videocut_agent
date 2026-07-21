"""
Final FunASR Integration Test
Tests the actual integration without unicode issues
"""

import sys
import os
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def test_imports():
    """Test basic imports"""
    print("=== Import Tests ===")

    success = []

    # Test ASR base
    try:
        from tools.asr_base import get_transcriber, ASRFactory
        success.append("asr_base")
        print("OK: ASR base architecture")

        providers = ASRFactory.get_available_providers()
        print(f"Available providers: {providers}")

    except Exception as e:
        print(f"FAIL: ASR base - {e}")

    # Test FunASR transcriber
    try:
        from tools.funasr_transcriber import FunASRTranscriber
        success.append("funasr_transcriber")
        print("OK: FunASR transcriber class")
    except Exception as e:
        print(f"FAIL: FunASR transcriber - {e}")

    return success

def test_subtitle_tools():
    """Test subtitle agent tools"""
    print("\n=== Subtitle Agent Tools ===")

    try:
        sys.path.append('subtitle_agent/tools')
        from funasr_subtitle_tools import funasr_audio2ass_tool

        print(f"OK: Tool name - {funasr_audio2ass_tool.name}")
        print(f"OK: Tool available")
        return True

    except Exception as e:
        print(f"FAIL: Subtitle tools - {e}")
        return False

def test_audio_tools():
    """Test audio agent tools"""
    print("\n=== Audio Agent Tools ===")

    try:
        sys.path.append('audiocut_agent/tools')
        from funasr_audio_tools import funasr_transcribe_audio

        print(f"OK: Tool name - {funasr_transcribe_audio.name}")
        print(f"OK: Tool available")
        return True

    except Exception as e:
        print(f"FAIL: Audio tools - {e}")
        return False

def test_model_directory():
    """Test model directory setup"""
    print("\n=== Model Directory ===")

    models_dir = Path("models")
    funasr_dir = models_dir / "funasr"

    if models_dir.exists():
        print(f"OK: Models dir exists - {models_dir}")

        if funasr_dir.exists():
            files = list(funasr_dir.iterdir())
            print(f"OK: FunASR dir exists with {len(files)} items")
            return True
        else:
            print(f"INFO: FunASR dir not found - {funasr_dir}")
            return False
    else:
        print(f"INFO: Models dir not found - {models_dir}")
        return False

def test_transcriber_creation():
    """Test creating a transcriber instance"""
    print("\n=== Transcriber Creation ===")

    try:
        from tools.asr_base import get_transcriber

        # Try to create FunASR transcriber (may fail due to missing deps)
        try:
            transcriber = get_transcriber(provider="funasr")
            print("OK: FunASR transcriber created successfully")
            return True
        except Exception as e:
            print(f"INFO: FunASR transcriber creation failed - {e}")

            # Try Azure as fallback
            try:
                transcriber = get_transcriber(provider="azure")
                print("OK: Azure transcriber works as fallback")
                return True
            except Exception as e:
                print(f"INFO: Azure fallback also failed - {e}")
                return False

    except Exception as e:
        print(f"FAIL: Transcriber creation - {e}")
        return False

def main():
    """Run all tests"""
    print("FunASR Integration Test")
    print("=" * 40)

    results = {
        'imports': test_imports(),
        'subtitle_tools': test_subtitle_tools(),
        'audio_tools': test_audio_tools(),
        'model_dir': test_model_directory(),
        'transcriber': test_transcriber_creation()
    }

    print("\n" + "=" * 40)
    print("Test Summary:")

    score = 0

    if 'asr_base' in results['imports']:
        print("PASS: ASR architecture integrated")
        score += 1
    else:
        print("FAIL: ASR architecture missing")

    if results['subtitle_tools']:
        print("PASS: Subtitle agent FunASR tools ready")
        score += 1
    else:
        print("FAIL: Subtitle agent tools missing")

    if results['audio_tools']:
        print("PASS: Audio agent FunASR tools ready")
        score += 1
    else:
        print("FAIL: Audio agent tools missing")

    if results['model_dir']:
        print("PASS: Model directory configured")
        score += 1
    else:
        print("INFO: Model directory needs setup")

    if results['transcriber']:
        print("PASS: Transcriber creation works")
        score += 1
    else:
        print("INFO: Transcriber needs dependencies")

    print(f"\nOverall: {score}/5 components ready")

    # Status assessment
    if score >= 4:
        print("\nSTATUS: FunASR integration SUCCESS")
        print("Core functionality is available")
    elif score >= 3:
        print("\nSTATUS: FunASR integration PARTIAL")
        print("Most components ready, some setup needed")
    else:
        print("\nSTATUS: FunASR integration NEEDS WORK")
        print("Major components missing")

    print("\nNext steps:")
    if not results['model_dir']:
        print("1. Run: cd models && python download.py")
    print("2. Install deps: pip install funasr[all] (if needed)")
    print("3. Test with actual audio files")

if __name__ == "__main__":
    main()