# ==============================================================================
# OSify ISO Builder Container (Arch Linux x86-64-v3 Toolchain)
# ==============================================================================
# Consente di compilare l'immagine ISO avviabile di OSify da qualsiasi sistema host
# (incluso macOS tramite Docker Desktop o macchine Linux senza archiso nativo).
# ==============================================================================

FROM archlinux:latest

# Aggiornamento keyring e pacchetti base di compilazione
RUN pacman -Syu --noconfirm --needed \
    archiso \
    base-devel \
    git \
    curl \
    wget \
    dosfstools \
    e2fsprogs \
    libisoburn \
    mtools \
    squashfs-tools \
    zstd

# Import chiavi repository CachyOS per microarchitettura x86-64-v3
RUN curl -s https://mirror.cachyos.org/cachyos-repo.tar.xz -o /tmp/cachyos-repo.tar.xz && \
    tar -xf /tmp/cachyos-repo.tar.xz -C /tmp/ && \
    cd /tmp/cachyos-repo && \
    pacman-key --recv-keys F3B60DE12716E5A0 2>/dev/null || true

WORKDIR /workspace

CMD ["/bin/bash", "/workspace/build/build-iso.sh", "build"]
