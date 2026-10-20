# Arch Linux local package

Build a pacman package from the current **committed** source tree:

```sh
bash packaging/arch/build-local.sh
sudo pacman -U /tmp/ballonstranslator-pkg.XXXXXX/ballonstranslator-local-*.pkg.tar.zst
```

Use the directory printed by the build command. This is a local package, not an
official Arch repository or AUR submission. `pacman -R ballonstranslator-local`
removes installed code and the launcher; it does not remove user data.

`ballonstranslator` launches the installed source under `/usr/share/ballonstranslator`.
Writable state is under `${XDG_DATA_HOME:-$HOME/.local/share}/ballonstranslator`.
On a new installation the first launch downloads Python 3.12 and core Python
dependencies using uv. Backend dependencies and model weights use the existing
in-app installer. These are user-managed downloads, not files owned by pacman.

To reuse an existing checkout, before the first launch copy its `config/` into
the state directory and link `.venv` and `data/models` to their existing locations.
Keep the original checkout while these links are in use. Never recursively remove
a linked model/library directory. Config files contain credentials; keep their
permissions private and never include them in the source archive.

This fork adds `Kazakh` to LLMTranslator and CBZ opening through the folder menu,
drag-and-drop, or `--proj-dir chapter.cbz`. CBZ images are naturally sorted and
imported into a persistent `chapter.ballons-<hash>` folder beside the archive.
Reopening the same archive reuses that project and preserves manual edits. The
original archive is unchanged. Finished pages use the editor's usual `result/`
output; exporting a translated CBZ is not implemented.
