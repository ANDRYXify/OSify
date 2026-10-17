#!/usr/bin/env bash
# ==============================================================================
# OSify Terminal Identity Banner (osify-fetch)
# ==============================================================================
# Mostra il logo ufficiale OSify in ANSI art e le statistiche di sistema a basso livello:
# Palette colori estratta dal logo: Viola profondo (#9333EA) e Verde Fluo (#4ADE80)
# ==============================================================================

set -euo pipefail

C_PURPLE='\033[38;2;147;51;234m'
C_MINT='\033[38;2;74;222;128m'
C_MAGENTA='\033[38;2;232;121;249m'
C_GRAY='\033[38;2;148;163;184m'
C_RESET='\033[0m'
C_BOLD='\033[1m'

printf "%b\n" "
${C_PURPLE}${C_BOLD}      .OOOOOOOOOOOO.          ${C_MINT}${C_BOLD}OSify Bare-Metal Universale${C_RESET}
${C_PURPLE}${C_BOLD}    .OOOOOOOOOOOOOOOO.        ${C_GRAY}---------------------------${C_RESET}
${C_PURPLE}${C_BOLD}   .OOOO'        'OOOO.       ${C_PURPLE}Creatore    : ${C_MAGENTA}Andrea Taliento (ANDRYXify)${C_RESET}
${C_PURPLE}${C_BOLD}  .OOOO'          'OOOO.      ${C_PURPLE}Nucleo      : ${C_RESET}$(uname -r 2>/dev/null || echo 'OSify-Core vA.0')
${C_PURPLE}${C_BOLD} .OOOO'            'OOOO.     ${C_PURPLE}Pianificatore: ${C_MINT}Priorità Adattiva (Latenza Minima)${C_RESET}
${C_PURPLE}${C_BOLD} OOOO'   ${C_MAGENTA}by Andryx${C_PURPLE}  'OOOO     ${C_PURPLE}Interfaccia : ${C_RESET}Motore Grafico Obsidian Dark Glass${C_RESET}
${C_PURPLE}${C_BOLD} 'OOOO.            .OOOO'     ${C_PURPLE}Rete Shaper : ${C_MINT}Anti-Bufferbloat DSCP${C_RESET}
${C_PURPLE}${C_BOLD}  'OOOO.          .OOOO'      ${C_PURPLE}Audio Engine: ${C_RESET}OSify Pro-Audio (<2.5ms)${C_RESET}
${C_PURPLE}${C_BOLD}   'OOOO.        .OOOO'       ${C_PURPLE}Flussi VOD  : ${C_MINT}Separazione Multicanale Ns-Safe${C_RESET}
${C_PURPLE}${C_BOLD}    'OOOOOOOOOOOOOOOO'        ${C_PURPLE}Compatibilità: ${C_RESET}Nativa PE (.exe) • APK • Mach-O • WASM${C_RESET}
${C_PURPLE}${C_BOLD}      'OOOOOOOOOOOO'          ${C_PURPLE}Architettura: ${C_MINT}Naked Skin Silicio-Diretto${C_RESET}
"

