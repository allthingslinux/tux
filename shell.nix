{ pkgs ? import <nixpkgs> {}, self ? null  }:

pkgs.mkShell {
  buildInputs = if self == null then [] else [
    self.packages.${pkgs.system}.envrc
  ];

  packages = with pkgs; [
    python313
    uv
    git
    jq
  ];

  shellHook = ''
    # See perSystem.packages.envrc
    if command -v envrc >/dev/null 2>&1; then
      envrc
    fi

    # Enters the user's preferred shell using a more robust method
    $(getent passwd $(id -un) | cut -d: -f7 | tr -d '\n')

    # Exits after child shell exits
    exit
  '';
}
