#!/usr/bin/env bash
# One-shot: print one stats line to stdout. Exit 1 on failure.
set -euo pipefail

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

read -r rx tx        < <(_net)
read -r mt mu mf mc  < <(_mem)

printf '%s rx=%s tx=%s mem_total_mb=%s mem_used_mb=%s mem_free_mb=%s mem_compressed_mb=%s\n' \
  "$(date '+%Y-%m-%d %H:%M:%S')" "$rx" "$tx" "$mt" "$mu" "$mf" "$mc"
