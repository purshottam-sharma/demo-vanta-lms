"""Stub: delegates to real bash_guard at project root."""
import subprocess, sys, os
real = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'agents', 'shared', 'hooks', 'bash_guard.py'))
data = sys.stdin.read()
r = subprocess.run([sys.executable, real], input=data, text=True, capture_output=True)
if r.stderr:
    print(r.stderr, file=sys.stderr)
sys.exit(r.returncode)
