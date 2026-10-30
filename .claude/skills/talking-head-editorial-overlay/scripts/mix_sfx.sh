#!/usr/bin/env bash
# Lay the sound-effect track under the voice (the same mix in every skill):
#   the voice passes through untouched; the SFX track takes GAIN dB, then ducks a further ~6–8 dB whenever someone is
#   speaking (sidechain on the voice), so effects sit behind the words and come up a little only in the pauses.
# usage: mix_sfx.sh <voice: audio or video file> <sfx_track.wav> <out.wav> [gain_db=0]
set -euo pipefail
V=$1 S=$2 O=$3 G=${4:-0}
ffmpeg -y -loglevel error -i "$V" -i "$S" -filter_complex \
  "[0:a]aformat=sample_fmts=fltp:channel_layouts=stereo,aresample=48000,asplit=2[v][key];\
[1:a]aformat=sample_fmts=fltp:channel_layouts=stereo,aresample=48000,volume=${G}dB[s0];\
[s0][key]sidechaincompress=threshold=0.03:ratio=4:attack=5:release=350[s];\
[v][s]amix=inputs=2:normalize=0:duration=first[m]" -map "[m]" -c:a pcm_s16le "$O"
