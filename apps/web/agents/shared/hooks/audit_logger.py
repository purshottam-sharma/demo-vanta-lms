"""Stub: delegates to real audit_logger at project root."""
import subprocess, sys, os
real = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'agents', 'shared', 'hooks', 'audit_logger.py'))
data = sys.stdin.read()
subprocess.run([sys.executable, real], input=data, text=True, capture_output=True)
sys.exit(0)
