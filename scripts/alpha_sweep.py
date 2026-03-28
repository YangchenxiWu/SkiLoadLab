# Backward-compatible shim that forwards to the maintained SkiLoadLab package.

from skiloadlab.core_sweep import main

if __name__ == "__main__":
    main()
