A Fedora RPM build of the Aurora Apple Silicon Linux kernel (aurora-silicon/linux,
LLVM=1, Rust enabled, built in a fedora:44 container on a GitHub arm64 runner)
failed. You get the end of the build log and our config fragment.

In GitHub markdown, briefly: the first real error (quote it), its likely cause
(our patches, our config fragment, an upstream break, the runner running out
of disk/time, or a network problem), and the smallest fix. Say clearly when
you are unsure; a human decides.
