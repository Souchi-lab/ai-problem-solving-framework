#!/usr/bin/env bash
# Resident monitor: collect stats every INTERVAL seconds.
# Log rotation: new file every ROTATE_MINUTES minutes.
# Old logs beyond KEEP_HOURS hours are deleted automatically.
#
# Usage:
#   ./net-mem-monitor.sh [LOG_DIR [INTERVAL [ROTATE_MINUTES [KEEP_HOURS]]]]
#
# Defaults: LOG_DIR=$HOME/logs  INTERVAL=60  ROTATE_MINUTES=60  KEEP_HOURS=24
#
# Stop: kill $(cat "$LOG_DIR/.monitor.pid")  or  Ctrl-C

set -euo pipefail

LOG_DIR="${1:-$HOME/logs}"
INTERVAL="${2:-60}"
ROTATE_MINUTES="${3:-60}"
KEEP_HOURS="${4:-24}"

mkdir -p "$LOG_DIR"
echo $$ > "$LOG_DIR/.monitor.pid"
trap 'rm -f "$LOG_DIR/.monitor.pid"; echo "[monitor] stopped."; exit 0' INT TERM

_net() {
  netstat -ibn 2>/dev/null | awk '
    NR==1 { for(i=1;i<=NF;i++) { if($i=="Name") nc=i; if($i=="Ibytes") ic=i; if($i=="Obytes") oc=i } next }
    !nc||!ic||!oc { exit 1 }
    $nc=="Name"||$nc=="lo0"||seen[$nc]++ { next }
    $ic~/^[0-9]+$/&&$oc~/^[0-9]+$/ { rx+=$ic; tx+=$oc }
    END { if(!ic||!oc) exit 1; printf "%s %s\n", rx+0, tx+0 }'
}

_mem() {
  local total_bytes
  total_bytes="$(sysctl -n hw.memsize)" || return 1
  vm_stat 2>/dev/null | awk -v tb="$total_bytes" '
    /page size of/           { match($0,/[0-9]+/); ps=substr($0,RSTART,RLENGTH)+0 }
    /Pages free:/            { gsub("\\.","",  $3); fr=$3 }
    /Pages active:/          { gsub("\\.","",  $3); ac=$3 }
    /Pages inactive:/        { gsub("\\.","",  $3); ia=$3 }
    /Pages speculative:/     { gsub("\\.","",  $3); sp=$3 }
    /Pages wired down:/      { gsub("\\.","",  $4); wi=$4 }
    /Pages occupied by compressor:/ { gsub("\\.","", $5); co=$5 }
    END {
      if(!ps) ps=4096
      m=1024*1024
      printf "%.1f %.1f %.1f %.1f\n",
        tb/m, (ac+ia+wi+co)*ps/m, (fr+sp)*ps/m, co*ps/m
    }'
}

_rotation_key() {
  # Round down to ROTATE_MINUTES boundary: e.g. 60min -> hourly, 10min -> every 10min
  local epoch min_epoch
  epoch="$(date +%s)"
  min_epoch=$(( (epoch / (ROTATE_MINUTES * 60)) * (ROTATE_MINUTES * 60) ))
  date -r "$min_epoch" '+%Y%m%d%H%M' 2>/dev/null \
    || date -d "@$min_epoch" '+%Y%m%d%H%M' 2>/dev/null \
    || date '+%Y%m%d%H%M'
}

_purge_old_logs() {
  local cutoff
  cutoff=$(( $(date +%s) - KEEP_HOURS * 3600 ))
  for f in "$LOG_DIR"/network_*.log; do
    [ -f "$f" ] || continue
    local mtime
    mtime="$(date -r "$f" +%s 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo 0)"
    if [ "$mtime" -lt "$cutoff" ]; then
      rm -f "$f"
      echo "[monitor] purged: $f"
    fi
  done
}

echo "[monitor] started — interval=${INTERVAL}s rotate=${ROTATE_MINUTES}min keep=${KEEP_HOURS}h log=${LOG_DIR}"

while true; do
  key="$(_rotation_key)"
  logfile="$LOG_DIR/network_${key}.log"

  if read -r rx tx       < <(_net) && \
     read -r mt mu mf mc < <(_mem); then
    printf '%s rx=%s tx=%s mem_total_mb=%s mem_used_mb=%s mem_free_mb=%s mem_compressed_mb=%s\n' \
      "$(date '+%Y-%m-%d %H:%M:%S')" "$rx" "$tx" "$mt" "$mu" "$mf" "$mc" \
      | tee -a "$logfile"
  else
    echo "[monitor] WARNING: failed to collect stats at $(date '+%Y-%m-%d %H:%M:%S')" >&2
  fi

  _purge_old_logs

  sleep "$INTERVAL"
done
